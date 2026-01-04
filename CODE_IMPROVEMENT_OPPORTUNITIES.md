# 🎯 Code Improvement Opportunities

**Date:** January 4, 2026
**Status:** Identified (Ready for Implementation)

---

## Overview

После рефакторинга TimestampedModel обнаружены дополнительные возможности для уменьшения дублирования кода и улучшения архитектуры.

---

## 🔴 HIGH PRIORITY

### 1. Base Response Schema
**Location:** `src/app/schemas/`
**Issue:** Множество schemas содержат повторяющиеся поля `created_at`, `updated_at`, `active`

**Current State:**
```python
# slot.py
class SlotInfo(BaseModel):
    id: int
    active: bool
    created_at: datetime
    updated_at: datetime

# tables.py
class TableInfo(BaseModel):
    id: int
    active: bool
    created_at: datetime
    updated_at: datetime

# media.py
class MediaInfo(BaseModel):
    id: UUID
    active: bool  # или missing
    created_at: datetime
    updated_at: datetime  # или missing
```

**Improvement:**
- Создать базовые schema классы с этими полями
- `TimestampedSchema` - для объектов с created_at, updated_at
- `ActiveSchema` - для объектов с active флагом
- `AuditedSchema` - для объектов со всеми тремя полями

**Expected Benefit:**
- Reduce 30+ duplicate field definitions across schema files
- Ensure consistency in response formats
- Single point of change for audit field definitions

**Estimation:** 2-3 hours (create 3 base schemas + update 8-10 schema files)

---

### 2. Common Service Patterns
**Location:** `src/app/services/`
**Issue:** Services повторяют одинаковые паттерны валидации и ошибок

**Current Duplications:**
```python
# Повторяется в multiple services:
async def _validate_exists(self, entity_id: int) -> ModelType:
    entity = await self.repository.get(entity_id)
    if not entity:
        raise ValidationException(ErrorCode.ENTITY_NOT_FOUND)
    return entity

async def _validate_active(self, entity: ModelType) -> None:
    if not entity.active:
        raise ValidationException(ErrorCode.ENTITY_INACTIVE)
```

**Improvement:**
- Создать `BaseService` mixin с методами валидации
- `EntityValidationMixin` со стандартными проверками
- Наследовать от него все сервисы

**Expected Benefit:**
- Reduce 50+ lines of duplicate validation code
- Consistent error handling across all services
- Easier to add new validation rules

**Estimation:** 2-3 hours (create mixin + update 7 services)

---

### 3. API Router Patterns
**Location:** `src/app/api/v1/*/router.py`
**Issue:** Повторяющиеся паттерны в endpoint definitions

**Current Example:**
```python
# Multiple routers follow same pattern:
@router.get("/{id}", response_model=SlotInfo)
async def get_slot(id: int, session: AsyncSession):
    repo = SlotRepository(session)
    entity = await repo.get(id)
    if not entity:
        raise EntityNotFoundException()
    return entity

@router.post("/", response_model=SlotInfo, status_code=201)
async def create_slot(data: SlotCreate, session: AsyncSession):
    repo = SlotRepository(session)
    service = SlotService(repo)
    return await service.create(data)
```

**Improvement:**
- Создать `BaseRouter` factory функцию
- Generic endpoint generator для стандартных CRUD операций
- Переопределять только специальные endpoints

**Expected Benefit:**
- Reduce ~200 lines of router boilerplate code
- Consistent error responses across all endpoints
- Easier to add new endpoints for new models

**Estimation:** 3-4 hours (create factory + refactor 5-6 routers)

---

## 🟡 MEDIUM PRIORITY

### 4. Error Response Standardization
**Location:** `src/app/core/exceptions.py`
**Issue:** Response format может быть более консистентным

**Improvement:**
```python
# Create standard response format:
class ErrorResponse(BaseModel):
    error: dict = {
        'code': str,
        'message': str,
        'timestamp': datetime,
        'path': str,
        'method': str,
    }
    request_id: str  # для трейсинга

# Exception should use this format
```

**Estimation:** 1-2 hours

---

### 5. Constants Consolidation
**Location:** `src/app/core/constants.py`
**Issue:** Много разных enum/dict структур, можно унифицировать

**Improvement:**
- Стандартизировать как хранятся error codes, messages
- Создать helper методы для часто используемых паттернов
- Документировать patterns for adding new constants

**Estimation:** 1-2 hours

---

## 🟢 LOW PRIORITY (Nice to Have)

### 6. Validation Utilities Consolidation
**Location:** `src/app/core/` - create `validators.py`
**Issue:** Validation logic разбросана по разным файлам

**Improvement:**
```python
# src/app/core/validators.py
async def validate_cafe_exists(session, cafe_id: int) -> Cafe:
    """Reusable validator for cafe existence"""

async def validate_entity_active(entity: TimestampedModel) -> None:
    """Reusable validator for active status"""

async def validate_time_range(start: time, end: time) -> None:
    """Reusable validator for time ranges"""
```

**Estimation:** 2-3 hours

---

### 7. Logger Configuration Consolidation
**Location:** `src/app/core/`
**Issue:** Logging setup может быть более централизован

**Improvement:**
- Create `logging_config.py` с setup для всех модулей
- Consistent log format across project
- Separate loggers for different modules

**Estimation:** 1-2 hours

---

## 📊 Impact Summary

| Improvement | Duplication Lines | Implementation Hours | Priority |
|------------|------------------|-------------------| ---------|
| Base Schemas | 30+ | 2-3 | 🔴 High |
| Service Mixins | 50+ | 2-3 | 🔴 High |
| Router Factory | 200+ | 3-4 | 🔴 High |
| Error Responses | 20+ | 1-2 | 🟡 Medium |
| Constants | 15+ | 1-2 | 🟡 Medium |
| Validators | 25+ | 2-3 | 🟢 Low |
| Logger Config | 10+ | 1-2 | 🟢 Low |
| **TOTAL** | **350+ lines** | **13-19 hours** | - |

---

## 🎯 Recommended Implementation Order

1. **Week 1 (Priority 1):** Base Schemas (most used, biggest impact)
2. **Week 1 (Priority 2):** Service Validation Mixin (impacts many files)
3. **Week 2 (Priority 3):** Router Factory (large refactor, can be done in parallel)
4. **Week 2 (Priority 4):** Other improvements as time permits

---

## ✅ Already Completed

- ✅ `TimestampedModel` base class (models field consolidation)
- ✅ `BaseCRUD` repository pattern (CRUD consolidation)

---

## Notes

- All improvements maintain backward compatibility
- No database migrations required
- Can be done incrementally without blocking other work
- Each improvement is independent (can be done in any order)
