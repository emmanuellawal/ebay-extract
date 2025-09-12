"""LLM extraction with offline fallback."""

import os
import base64
import logging
from pathlib import Path
from typing import List, Dict, Any
from .models import IntakeBundle, Item, LotMetadata, Media, Pricing, Shipping

logger = logging.getLogger(__name__)

def extract_bundle(case_id: str, image_paths: List[Path], hints: Dict[str, Any], config: Dict[str, Any]) -> IntakeBundle:
    """
    Extract IntakeBundle from case data with LLM or offline fallback.
    
    Args:
        case_id: Unique case identifier
        image_paths: List of image file paths
        hints: Dictionary of hints from JSON files
        config: Configuration dictionary
        
    Returns:
        IntakeBundle with extracted items
    """
    if config["llm"]["enabled"]:
        return _extract_with_llm(case_id, image_paths, hints, config)
    else:
        return _extract_offline_fallback(case_id, image_paths, hints)

def _extract_offline_fallback(case_id: str, image_paths: List[Path], hints: Dict[str, Any]) -> IntakeBundle:
    """
    Create deterministic fallback IntakeBundle without LLM.
    
    Args:
        case_id: Unique case identifier
        image_paths: List of image file paths
        hints: Dictionary of hints from JSON files
        
    Returns:
        IntakeBundle with deterministic items
    """
    logger.info(f"Using offline fallback for case: {case_id}")
    
    # Create default lot metadata
    lot_metadata = LotMetadata(
        lot_id=case_id,
        list_strategy="individual",
        notes="Generated offline"
    )
    
    # Convert image paths to Media objects
    photos = []
    for i, img_path in enumerate(image_paths):
        media = Media(
            source="file",
            path=str(img_path),
            alt=f"Image {i+1}"
        )
        photos.append(media)
    
    items = []
    
    # Check if hints suggest single item
    if hints and _is_single_item_hint(hints):
        # Build single item from hints
        item = _build_item_from_hints(case_id, hints, photos)
        items.append(item)
    else:
        # Create generic item
        sku = f"{case_id}-001"
        item = Item(
            sku=sku,
            title=hints.get("title", "Unlabeled Item"),
            category_hint="generic",
            condition_grade="Good",
            photos=photos,
            pricing=Pricing(),
            shipping=Shipping()
        )
        items.append(item)
    
    return IntakeBundle(
        case_id=case_id,
        lot_metadata=lot_metadata,
        items=items
    )

def _extract_with_llm(case_id: str, image_paths: List[Path], hints: Dict[str, Any], config: Dict[str, Any]) -> IntakeBundle:
    """
    Extract IntakeBundle using LLM (OpenAI).
    
    Args:
        case_id: Unique case identifier
        image_paths: List of image file paths
        hints: Dictionary of hints from JSON files
        config: Configuration dictionary
        
    Returns:
        IntakeBundle with LLM-extracted items
    """
    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage
        
        # Initialize OpenAI
        llm = ChatOpenAI(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"]
        )
        
        # Build prompt
        system_prompt = """You are an expert estate cataloger. Analyze the provided images and hints to create accurate product listings.
        
        Be conservative in your assessments. Focus on one category block per item. Support lot listings when appropriate.
        
        Return a structured IntakeBundle with case_id, lot_metadata, and items array."""
        
        # Prepare images as base64
        image_data = []
        for img_path in image_paths:
            try:
                with open(img_path, 'rb') as f:
                    img_bytes = f.read()
                    img_b64 = base64.b64encode(img_bytes).decode()
                    image_data.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                    })
            except Exception as e:
                logger.warning(f"Failed to read image {img_path}: {e}")
        
        # Build human message
        hints_text = f"Hints: {hints}" if hints else "No hints provided."
        
        content = [{"type": "text", "text": f"{system_prompt}\n\n{hints_text}"}]
        content.extend(image_data)
        
        message = HumanMessage(content=content)
        
        # Get structured output
        structured_llm = llm.with_structured_output(IntakeBundle)
        result = structured_llm.invoke([message])
        
        # Ensure case_id and defaults
        result.case_id = case_id
        if not result.lot_metadata:
            result.lot_metadata = LotMetadata(
                lot_id=case_id,
                list_strategy="individual"
            )
        
        return result
        
    except Exception as e:
        logger.warning(f"LLM extraction failed: {e}. Falling back to offline mode.")
        return _extract_offline_fallback(case_id, image_paths, hints)

def _is_single_item_hint(hints: Dict[str, Any]) -> bool:
    """Check if hints suggest a single item."""
    return (
        "title" in hints or
        "brand" in hints or
        "model" in hints or
        any(key in hints for key in ["book", "electronics", "vehicle", "card", "apparel"])
    )

def _build_item_from_hints(case_id: str, hints: Dict[str, Any], photos: List[Media]) -> Item:
    """Build Item from hints dictionary."""
    sku = f"{case_id}-001"
    
    # Extract basic info
    title = hints.get("title", "Item from Hints")
    brand = hints.get("brand")
    model = hints.get("model")
    category_hint = hints.get("category_hint", "generic")
    condition_grade = hints.get("condition_grade", "Good")
    
    # Create item
    item = Item(
        sku=sku,
        title=title,
        brand=brand,
        model=model,
        category_hint=category_hint,
        condition_grade=condition_grade,
        photos=photos,
        pricing=Pricing(),
        shipping=Shipping()
    )
    
    # Add category-specific data
    if "book" in hints:
        item.book = hints["book"]
    elif "electronics" in hints:
        item.electronics = hints["electronics"]
    elif "vehicle" in hints:
        item.vehicle = hints["vehicle"]
    elif "card" in hints:
        item.card = hints["card"]
    elif "apparel" in hints:
        item.apparel = hints["apparel"]
    
    return item
