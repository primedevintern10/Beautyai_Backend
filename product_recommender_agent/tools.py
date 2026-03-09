# product_recommender_agent/tools.py
import logging
from typing import Optional, Dict, Any, List
from pymongo import DESCENDING
from langchain_core.tools import tool
from config.database import product_collection

logger = logging.getLogger(__name__)

_collection = product_collection
_keywords_cache: Dict[str, List[str]] = {}   # populated on first call, reused after

_KEYWORD_FIELDS = ["category", "concerns", "skin_types", "hair_types", "exclusions", "brand"]

# Fields fetched from MongoDB — rich enough for routine agent, excludes reviews and audit timestamps
_ROUTINE_FIELDS = {
    "_id": 0,
    "id": 1, "name": 1, "brand": 1,
    "description": 1, "howToUse": 1, "imageUrl": 1,
    "category": 1, "subcategory": 1, "routineStep": 1,
    "price": 1, "skin_types": 1, "hair_types": 1,
    "concerns": 1, "ingredients": 1, "exclusions": 1,
    "texture": 1, "averageRating": 1, "reviewCount": 1,
    "isBestseller": 1, "reviews": 1,
}


async def init_keywords_cache() -> None:
    """Pre-warm the keywords cache at startup so the first user pays no DB cost."""
    from collections import defaultdict
    logger.info("[init_keywords_cache] Pre-warming keywords cache...")
    try:
        unique_values: Dict[str, set] = defaultdict(set)
        async for doc in _collection.find({}, {f: 1 for f in _KEYWORD_FIELDS}):
            for f in _KEYWORD_FIELDS:
                value = doc.get(f)
                if isinstance(value, list):
                    unique_values[f].update(v for v in value if v is not None)
                elif value is not None:
                    unique_values[f].add(value)
        _keywords_cache.update({
            f: sorted([str(v) for v in unique_values[f]]) for f in _KEYWORD_FIELDS
        })
        logger.info(f"[init_keywords_cache] Done — cached fields: {list(_keywords_cache.keys())}")
    except Exception as e:
        logger.error(f"[init_keywords_cache] Failed: {e}", exc_info=True)



def _build_query(
    concern: str,
    _: str,
    allergy: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Build MongoDB query using concern, category, and allergy only."""
    query: Dict[str, Any] = {
        "concerns": {"$elemMatch": {"$regex": concern, "$options": "i"}},
    }

    # Category filter (exact match, case-insensitive)
    if category:
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}

    # Allergy exclusion (skip if "none" or empty)
    if allergy and allergy.lower() != "none":
        query["exclusions"] = {
            "$not": {"$elemMatch": {"$regex": allergy, "$options": "i"}}
        }

    return query


def _format_products(products: List[Dict[str, Any]]) -> str:
    """Format product list for readable output."""
    if not products:
        return "No matching products found."

    lines = []
    for p in products:
        name = p.get('name', 'Unknown Product')
        brand = p.get('brand', 'Unknown Brand')
        category = p.get('category', 'N/A')
        rating = p.get('averageRating', 'N/A')
        desc = p.get('description', 'No description')[:150] + '...' if len(p.get('description', '')) > 150 else p.get('description', 'N/A')
        how_to = p.get('howToUse', 'No usage info')[:100] + '...' if len(p.get('howToUse', '')) > 100 else p.get('howToUse', 'N/A')

        lines.append(
            f"- **{name}** by {brand}\n"
            f"  Category: {category} | Rating: {rating} ⭐\n"
            f"  Description: {desc}\n"
            f"  How to use: {how_to}"
        )
    return "\n\n".join(lines)


@tool
async def query_products(
    concern: str,
    skin_hair_type: str,
    allergy: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search BeautyMart products for the best match.

    Parameters:
    - concern: main skin/hair concern (required)
    - skin_hair_type: skin or hair type (required)
    - allergy: ingredient to avoid, or "none" (optional)
    - category: main category (face, hair, body, baby, etc.) — highly recommended (optional)

    Returns JSON with top products or status message.
    """
    logger.info(
        f"[QUERY IN] concern={concern!r} | type={skin_hair_type!r} | "
        f"allergy={allergy!r} | category={category!r}"
    )

    try:
        # Sort: rating → trending → purchases → bestseller
        sort_order = [
            ("averageRating", DESCENDING),
            ("trendingScore", DESCENDING),
            ("purchaseCount", DESCENDING),
            ("isBestseller", DESCENDING),
        ]

        results: List[Dict[str, Any]] = []
        seen_names: set = set()
        used_paths: List[str] = []

        def _merge(new_docs: List[Dict[str, Any]]) -> None:
            for doc in new_docs:
                name = doc.get("name")
                if name not in seen_names:
                    seen_names.add(name)
                    results.append(doc)

        # Primary: concern + category + allergy
        query = _build_query(concern, skin_hair_type, allergy, category)
        primary = await _collection.find(query, _ROUTINE_FIELDS).sort(sort_order).limit(10).to_list(10)
        _merge(primary)
        used_paths.append("primary")

        # Fallback 1: drop allergy if still under 10
        if len(results) < 10 and allergy and allergy.lower() != "none":
            logger.info(f"[QUERY FALLBACK 1] {len(results)}/10 — retrying without allergy ({allergy!r})")
            query = _build_query(concern, skin_hair_type, None, category)
            fb1 = await _collection.find(query, _ROUTINE_FIELDS).sort(sort_order).limit(10).to_list(10)
            _merge(fb1)
            used_paths.append("fallback-1 (no allergy)")

        # Fallback 2: concern only — drop category too
        if len(results) < 10:
            logger.info(f"[QUERY FALLBACK 2] {len(results)}/10 — retrying concern-only ({concern!r})")
            query = {"concerns": {"$elemMatch": {"$regex": concern, "$options": "i"}}}
            fb2 = await _collection.find(query, _ROUTINE_FIELDS).sort(sort_order).limit(10).to_list(10)
            _merge(fb2)
            used_paths.append("fallback-2 (concern only)")

        if not results:
            logger.info(f"[QUERY OUT] No products found after all fallbacks | concern={concern!r}")
            return {
                "status": "no_match",
                "message": f"No products found for '{concern}' + '{skin_hair_type}'. Try a different keyword or type."
            }

        top_products = results[:10]
        formatted = _format_products(top_products)

        logger.info(
            f"[QUERY OUT] Paths: {' → '.join(used_paths)} | Total: {len(results)} | Showing: {len(top_products)}\n"
            + "\n".join(
                f"  [{i+1}] {p.get('name', 'N/A')} by {p.get('brand', 'N/A')} "
                f"| Rating: {p.get('averageRating', 'N/A')}"
                for i, p in enumerate(top_products)
            )
        )

        return {
            "status": "success",
            "formatted": formatted,
            "products": top_products,
            "count": len(results),
            "used_category": category if category else "inferred/auto"
        }

    except Exception as e:
        logger.error(f"[QUERY ERROR] {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": "Database error — could not retrieve products right now."
        }