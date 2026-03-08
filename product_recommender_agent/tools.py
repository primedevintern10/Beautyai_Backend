# product_recommender_agent/tools.py
import logging
from typing import Optional, Dict, Any, List
from pymongo import DESCENDING
from langchain_core.tools import tool
from config.database import product_collection

logger = logging.getLogger(__name__)

_collection = product_collection


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
        f"Query received: concern={concern!r}, type={skin_hair_type!r}, "
        f"allergy={allergy!r}, category={category!r}"
    )

    try:
        query = _build_query(concern, skin_hair_type, allergy, category)

        # Sort: rating → trending → purchases → bestseller
        sort_order = [
            ("averageRating", DESCENDING),
            ("trendingScore", DESCENDING),
            ("purchaseCount", DESCENDING),
            ("isBestseller", DESCENDING),
        ]

        # Primary search
        results = await _collection.find(query).sort(sort_order).limit(10).to_list(10)

        # Fallback 1: drop allergy (keep concern + category)
        if not results and allergy and allergy.lower() != "none":
            logger.info("No results with allergy, retrying without allergy")
            query = _build_query(concern, skin_hair_type, None, category)
            results = await _collection.find(query).sort(sort_order).limit(10).to_list(10)

        # Fallback 2: concern only — no category, no allergy (last resort)
        if not results:
            logger.info("No results with category, retrying concern only")
            query = {"concerns": {"$elemMatch": {"$regex": concern, "$options": "i"}}}
            results = await _collection.find(query).sort(sort_order).limit(10).to_list(10)

        if not results:
            return {
                "status": "no_match",
                "message": f"No products found for '{concern}' + '{skin_hair_type}'. Try a different keyword or type."
            }

        # Take top 5 for response
        top_products = results[:5]
        formatted = _format_products(top_products)

        logger.info(
            f"Query returned {len(results)} results | Showing top {len(top_products)} | "
            f"Products: {[p.get('name', 'N/A') for p in top_products]}"
        )

        return {
            "status": "success",
            "products": top_products,
            "formatted": formatted,
            "count": len(results),
            "used_category": category if category else "inferred/auto"
        }

    except Exception as e:
        logger.error(f"Product query failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": "Database error — could not retrieve products right now."
        }