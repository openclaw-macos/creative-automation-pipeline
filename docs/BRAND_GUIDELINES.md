# NexaGoods Brand Guidelines

## Overview
NexaGoods is a global consumer goods brand offering premium essentials for modern living. Our brand identity balances professionalism with approachability, innovation with reliability.

## Brand Identity

### Logo
- **File**: `assets/nexagoods_logo.png`
- **Placement**: Top-right corner of all visual assets
- **Opacity**: 10% (0.1) - subtle watermark effect
- **Minimum size**: 5% of image width/height
- **Clear space**: Equal to logo height on all sides

### Color Palette

#### Primary Colors
- **Deep Blue** `#2A5CAA` - Primary brand color
  - Usage: Headlines, primary buttons, key visual elements
  - Represents: Trust, professionalism, reliability

- **Orange** `#FF6B35` - Secondary accent
  - Usage: Call-to-action elements, highlights, notifications
  - Represents: Energy, innovation, warmth

- **Green** `#34C759` - Accent color
  - Usage: Success states, natural/organic product lines
  - Represents: Freshness, sustainability, growth

#### Neutral Colors
- **Light Gray** `#F5F5F7` - Backgrounds
- **Dark Gray** `#1D1D1F` - Text and headlines

### Color Compliance Rules
1. At least one brand color must cover ≥3% of total image pixels
2. Color tolerance: ±8% RGB value variance allowed
3. Neutral colors don't count toward compliance minimums

## Typography

### Text Overlays (Video/Audio Assets)
- **Font size**: 48pt (scales with resolution)
- **Font color**: White `#FFFFFF`
- **Position**: Bottom-center of frame
- **Background**: 70% opacity black backdrop for readability
- **Animation**: 500ms fade-in, 500ms fade-out
- **Line length**: Maximum 40 characters per line

## Content Guidelines

### Prohibited Terminology
The following words/phrases are NEVER permitted in campaign messages:
- Absolute claims: "best", "fastest", "#1", "winner"
- Hyperbolic language: "amazing", "incredible", "revolutionary"
- Miracle claims: "magic", "miracle", "secret", "instant"
- Price-focused: "cheap", "free", "guarantee", "100%"

### Approved Messaging Tone
- Focus on product benefits, not hyperbolic claims
- Use evidence-based language
- Emphasize quality, design, and user experience
- Maintain professional yet approachable tone

## Visual Asset Standards

### Image Generation
- **Default size**: 512×512 pixels
- **Aspect ratios supported**: 1:1 (square), 16:9 (widescreen), 9:16 (vertical)
- **Prohibited sizes**: 1024×1024, 2048×2048 (or any 2048 dimension)
- **Quality**: Professional photography style, studio lighting
- **Background**: Clean, uncluttered, brand-color appropriate

### Video Standards
- **Resolution**: 1920×1080 (16:9) preferred
- **Frame rate**: 30 FPS
- **Background music**: Optional, royalty-free tracks only
- **Default**: Silent if no music provided
- **Logo placement**: Top-right corner, 10% opacity throughout

## Compliance Enforcement

### Automated Checks
All generated assets undergo automated compliance verification:

1. **Brand Color Check**
   - Verifies presence of brand colors (≥3% coverage)
   - Uses OpenCV with 8% RGB tolerance

2. **Logo Presence Check**
   - Confirms logo appears in top-right quadrant
   - Minimum 0.5% coverage with 75% match threshold

3. **Legal Guardrail**
   - Scans all text for prohibited terminology
   - Case-insensitive whole-word matching
   - Blocks non-compliant content pre-generation

### Manual Review Triggers
Assets are flagged for manual review if:
- Compliance check scores are borderline (within 20% of thresholds)
- Multiple compliance failures in same asset
- Legal guardrail detects borderline terminology

## Regional Considerations

### Approved Markets
- United States (US)
- European Union (EU)
- United Kingdom (UK)
- Canada (CA)
- Australia (AU)
- Japan (JP)

### Region-Specific Rules
- **EU**: Additional GDPR compliance text may be required
- **US**: FDA disclaimers for applicable product categories
- **JP**: Localized logos and sizing requirements

## Implementation Notes

### Creative Automation Pipeline
- All rules are codified in `configs/brand_config.json`
- Compliance modules: `src/brand_compliance.py`
- Legal guardrail: `src/legal_guardrail.py`
- Reporting: `src/reporting.py`

### Testing Compliance
```bash
# Test brand compliance on existing image
python src/brand_compliance.py outputs/images/sample.png

# Test legal guardrail on campaign message
python src/legal_guardrail.py "Your campaign message here"
```

### Updates to Guidelines
1. Update `brand_config.json` with new rules
2. Update this document to reflect changes
3. Test updated compliance checks
4. Deploy to automation pipeline

---

**Version**: 1.0  
**Last Updated**: 2026-03-22  
**Contact**: Brand Compliance Team