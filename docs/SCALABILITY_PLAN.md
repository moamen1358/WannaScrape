# WannaScrape Scalability Plan

## Project: Plugin-Based Bot Detection Architecture

**Status**: ✅ FULLY INTEGRATED
**Date**: January 2026
**Goal**: Create a scalable plugin system so adding new bot detections takes < 10 minutes with no core code changes.

**Result**: All phases complete. Plugin system integrated into `scraper.py`. 114 tests passing.

---

## Phase 1: Analysis & Design

### 1.1 Review Current Codebase ✅ DONE
- [x] Read `app/core/scraper.py` - identified bot detection at lines 341-371
- [x] Read `app/core/captcha_solver.py` - found monolithic if/else chains
- [x] Read `app/utils/cloudflare.py` - separate module pattern
- [x] Read `app/utils/human_behavior.py` - behavior simulation code
- [x] Read `app/services/advanced_anti_detection.py` - fingerprint spoofing

**Findings:**
| File | Problem |
|------|---------|
| `scraper.py:341-346` | Hardcoded Cloudflare import + inline detection |
| `scraper.py:350-355` | Tight coupling to CaptchaSolver |
| `captcha_solver.py:37-97` | Giant if/else chain for 5 CAPTCHA types |
| `captcha_solver.py:151-179` | Another if/else dispatcher |
| `cloudflare.py` | Different pattern than CAPTCHAs |

### 1.2 Design Base Class ✅ DONE
- [x] Define `BaseDetection` abstract class
- [x] Define `DetectionResult` dataclass
- [x] Define `DetectionCategory` enum (CHALLENGE, CAPTCHA, FINGERPRINT, BEHAVIORAL)
- [x] Define `SolveMethod` enum (WAIT, API, BEHAVIORAL, BYPASS, NONE)
- [x] Add helper methods for common operations

**Created**: `app/detections/base.py` (180 lines)

---

## Phase 2: Auto-Discovery System

### 2.1 Create Registry ✅ DONE
- [x] Implement singleton `DetectionRegistry` class
- [x] Auto-import all `.py` files in `app/detections/`
- [x] Find all `BaseDetection` subclasses
- [x] Register and sort by priority
- [x] Provide `detect_all()`, `solve()`, `list_all()` methods

**Created**: `app/detections/registry.py` (280 lines)

### 2.2 Create Handler ✅ DONE
- [x] High-level `DetectionHandler` class for scraper integration
- [x] `handle_detections(page, url)` method
- [x] `handle_by_category()` for selective detection
- [x] Backward compatibility functions for old Cloudflare API

**Created**: `app/detections/handler.py` (180 lines)

---

## Phase 3: Migrate Existing Detections

### 3.1 Cloudflare Detection ✅ DONE
- [x] Create `CloudflareDetection` class
- [x] Migrate selectors from `cloudflare.py`
- [x] Migrate title/content indicators
- [x] Implement wait-based solving
- [x] Set priority=10 (runs first)

**Created**: `app/detections/cloudflare.py` (120 lines)

### 3.2 reCAPTCHA Detection ✅ DONE
- [x] Create `RecaptchaDetection` class
- [x] Migrate from `captcha_solver.py`
- [x] Extract sitekey functionality
- [x] 2captcha and Capsolver integration
- [x] Solution injection

**Created**: `app/detections/recaptcha.py` (230 lines)

### 3.3 hCaptcha Detection ✅ DONE
- [x] Create `HcaptchaDetection` class
- [x] Migrate from `captcha_solver.py`
- [x] 2captcha and Capsolver integration

**Created**: `app/detections/hcaptcha.py` (160 lines)

### 3.4 PerimeterX Detection ✅ DONE
- [x] Create `PerimeterXDetection` class
- [x] Migrate Press & Hold logic
- [x] Behavioral mouse simulation
- [x] No API required

**Created**: `app/detections/perimeterx.py` (200 lines)

### 3.5 DataDome Detection ✅ DONE
- [x] Create `DataDomeDetection` class as example
- [x] Implement detection patterns
- [x] Wait-based + refresh solving strategy

**Created**: `app/detections/datadome.py` (150 lines)

---

## Phase 4: Testing

### 4.1 Unit Tests ✅ DONE
- [x] `TestDetectionResult` - 3 tests
- [x] `TestBaseDetection` - 3 tests
- [x] `TestDetectionRegistry` - 10 tests
- [x] `TestCloudflareDetection` - 3 tests
- [x] `TestRecaptchaDetection` - 2 tests
- [x] `TestPerimeterXDetection` - 1 test
- [x] `TestDetectionHandler` - 3 tests
- [x] `TestBackwardCompatibility` - 2 tests
- [x] `TestPluginIntegration` - 5 tests

**Created**: `tests/test_detections.py` (32 tests)

### 4.2 Verify Existing Tests ✅ DONE
- [x] Run all 82 original tests
- [x] Confirm no regressions
- [x] Total: **114 tests passing**

---

## Phase 5: Documentation

### 5.1 Plugin README ✅ DONE
- [x] Quick start guide
- [x] Architecture overview
- [x] Template for new detections
- [x] Priority guidelines
- [x] Configuration examples
- [x] Testing guide

**Created**: `app/detections/README.md` (400+ lines)

### 5.2 AI Instructions ✅ DONE
- [x] Create instructions for AI assistants
- [x] Step-by-step guide for adding detections

**Created**: `docs/AI_INSTRUCTIONS.md`

---

## Phase 6: Integration ✅ DONE

### 6.1 Update scraper.py ✅ DONE
- [x] Import `DetectionHandler` with fallback
- [x] Initialize handler in `__init__` (line 127-133)
- [x] Replace detection logic (lines 356-401)
- [x] Keep legacy fallback for backward compatibility
- [x] Add `get_detection_stats()` method
- [x] All 114 tests passing

**Changes made to scraper.py:**
- Lines 35-42: Added conditional import for DetectionHandler
- Lines 127-133: Initialize DetectionHandler in `__init__`
- Lines 356-401: New plugin-based detection with legacy fallback
- Lines 622-626: Added `get_detection_stats()` method

### 6.2 Update config.json ⏳ OPTIONAL
- [ ] Add `detections` section for per-detection config
- [ ] Configure API keys for CAPTCHA solving

**Note**: Config update is optional. System works with existing config.

---

## Files Created

```
app/detections/
├── __init__.py         ✅ Created
├── base.py             ✅ Created (BaseDetection, DetectionResult)
├── registry.py         ✅ Created (Auto-discovery)
├── handler.py          ✅ Created (High-level API)
├── README.md           ✅ Created (Documentation)
│
├── cloudflare.py       ✅ Created (Priority: 10)
├── recaptcha.py        ✅ Created (Priority: 30)
├── hcaptcha.py         ✅ Created (Priority: 35)
├── perimeterx.py       ✅ Created (Priority: 20)
└── datadome.py         ✅ Created (Priority: 25)

tests/
└── test_detections.py  ✅ Created (32 tests)

docs/
├── SCALABILITY_PLAN.md ✅ Created (This file)
└── AI_INSTRUCTIONS.md  ✅ Created
```

---

## Success Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Time to add new detection | < 10 min | ✅ ~5 min |
| Core code changes needed | 0 | ✅ 0 |
| Tests passing | 82+ | ✅ 114 |
| Backward compatible | Yes | ✅ Yes |
| Independent testing | Yes | ✅ Yes |

---

## How to Add New Detection

1. Create `app/detections/yourdetection.py`
2. Inherit from `BaseDetection`
3. Set `name`, `priority`, `category`
4. Implement `detect()` and `solve()`
5. Run tests: `pytest tests/test_detections.py -v`
6. Done! Auto-registered.

See `docs/AI_INSTRUCTIONS.md` for detailed guide.
