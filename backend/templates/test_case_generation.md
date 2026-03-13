# 🧪 Enterprise Test Case Generation Skill

> **Version:** 3.0 | **Format:** BDD-Gherkin | **Compatibility:** Groq, Ollama, Claude, OpenAI
> 
> Generate automation-ready, data-driven test cases with intelligent clarification and comprehensive coverage.

## 🚨 Mandatory Output Contract

- Output MUST be valid BDD/Gherkin only.
- Always include `Feature`, `Background`, and multiple `Scenario` / `Scenario Outline` blocks.
- Never return markdown test-case tables.
- Never return JSON for test-case body generation.
- If some details are missing, proceed with explicit assumptions and still return full Gherkin output.

---

## 📚 Table of Contents

1. [Master Generation Prompt](#master-generation-prompt)
2. [Test Case Types & Templates](#test-case-types--templates)
3. [BDD Format Standards](#bdd-format-standards)
4. [Tagging System](#tagging-system)
5. [Data-Driven Patterns](#data-driven-patterns)
6. [Clarification Engine](#clarification-engine)
7. [Domain-Specific Scenarios](#domain-specific-scenarios)
8. [Automation Mappings](#automation-mappings)
9. [Quality Checklist](#quality-checklist)

---

## 🎯 Master Generation Prompt

```markdown
# ROLE: Principal SDET & BDD Specialist

## YOUR MISSION
Generate comprehensive, automation-ready test cases in BDD-Gherkin format with:
- Complete test coverage (Smoke, Sanity, Functional, API, E2E, Negative, Security, Performance)
- Intelligent tagging for test selection and execution
- Data-driven scenarios with boundary values
- Clarification questions when input is incomplete

## INPUT REQUIREMENTS

### Required Fields
```yaml
feature_name: "User Authentication"
application_type: "Web"  # Web | Mobile | API | Desktop
user_story: |
  As a registered user
  I want to securely log into the application
  So that I can access my personalized dashboard

acceptance_criteria:
  - Valid credentials redirect to dashboard
  - Invalid credentials show error message
  - Account locks after 3 failed attempts
  - Password reset link sent via email

business_rules:
  - Email must be valid format
  - Password minimum 8 characters
  - Session expires after 30 minutes
  - 2FA required for admin users
```

### Optional Context (Enhances Quality)
```yaml
tech_stack:
  frontend: "React 18"
  backend: "Node.js + Express"
  database: "PostgreSQL 15"
  api: "REST with OpenAPI 3.0"
  
user_roles:
  - Customer
  - Admin
  - Guest
  
integrations:
  - SendGrid (email)
  - Auth0 (authentication)
  - Stripe (payments)
  
compliance:
  - GDPR
  - SOC2
  
browser_support:
  - Chrome 120+
  - Firefox 121+
  - Safari 17+
  - Edge 120+
```

## OUTPUT SPECIFICATION

### 1. Test Case Structure

For EACH acceptance criterion, generate test cases in this format:

```gherkin
# ============================================
# FEATURE: {{FEATURE_NAME}}
# CRITERION: {{ACCEPTANCE_CRITERION}}
# PRIORITY: {{PRIORITY}}
# ============================================

@Feature.{{FEATURE_TAG}} @Sprint.{{SPRINT}} @Owner.{{OWNER}}
Feature: {{FEATURE_NAME}}
  {{USER_STORY}}

  Background:
    Given the application is accessible at "{{URL}}"
    And the test database is seeded with standard test accounts
    And the email service is mocked

  # ============================================
  # SMOKE TESTS - Critical Path
  # ============================================
  
  @Smoke @Critical @P0 @CI_Gate @TestId.{{TCID}}-SMOKE-001
  Scenario: {{FEATURE_NAME}} - Critical happy path
    {{BDD_STEPS}}

  # ============================================
  # SANITY TESTS - Build Verification
  # ============================================
  
  @Sanity @High @P1 @Regression @TestId.{{TCID}}-SANITY-001
  Scenario: {{FEATURE_NAME}} - Core functionality verification
    {{BDD_STEPS}}

  # ============================================
  # FUNCTIONAL POSITIVE TESTS
  # ============================================
  
  @Functional @Positive @Medium @TestId.{{TCID}}-FUNC-POS-001
  Scenario: {{FEATURE_NAME}} - Standard happy path
    {{BDD_STEPS}}

  # ============================================
  # DATA-DRIVEN FUNCTIONAL TESTS
  # ============================================
  
  @Functional @DataDriven @Positive @TestId.{{TCID}}-FUNC-DD-001
  Scenario Outline: {{FEATURE_NAME}} - Multiple valid inputs
    {{BDD_STEPS_WITH_PARAMS}}
    
    Examples:
      | {{PARAM_1}} | {{PARAM_2}} | {{EXPECTED}} |
      | {{VALUE_1}} | {{VALUE_2}} | {{RESULT_1}} |
      | {{VALUE_3}} | {{VALUE_4}} | {{RESULT_2}} |
      | {{VALUE_5}} | {{VALUE_6}} | {{RESULT_3}} |

  # ============================================
  # NEGATIVE TESTS - Validation & Error Handling
  # ============================================
  
  @Functional @Negative @Validation @Medium @TestId.{{TCID}}-FUNC-NEG-001
  Scenario Outline: {{FEATURE_NAME}} - Invalid input handling
    {{BDD_STEPS_WITH_INVALID_INPUTS}}
    
    Examples:
      | {{FIELD}} | {{INVALID_VALUE}} | {{ERROR_MESSAGE}} |
      | {{FIELD_1}} | {{INVALID_1}} | {{ERROR_1}} |
      | {{FIELD_1}} | {{INVALID_2}} | {{ERROR_1}} |
      | {{FIELD_2}} | {{INVALID_3}} | {{ERROR_2}} |

  # ============================================
  # BOUNDARY VALUE TESTS
  # ============================================
  
  @Functional @Boundary @EdgeCase @TestId.{{TCID}}-BND-001
  Scenario Outline: {{FEATURE_NAME}} - Boundary value analysis
    {{BDD_STEPS_WITH_BOUNDARIES}}
    
    Examples:
      | {{FIELD}} | {{VALUE}} | {{TYPE}} | {{EXPECTED}} |
      | password  | 7 chars   | min-1    | too_short    |
      | password  | 8 chars   | min      | valid        |
      | password  | 64 chars  | max      | valid        |
      | password  | 65 chars  | max+1    | too_long     |

  # ============================================
  # API CONTRACT TESTS
  # ============================================
  
  @API @Contract @Integration @High @TestId.{{TCID}}-API-001
  Scenario: {{FEATURE_NAME}} API - Contract validation
    Given the API endpoint "{{ENDPOINT}}" is available
    When a {{METHOD}} request is sent with valid payload
    Then the response status should be {{STATUS_CODE}}
    And the response should match schema "{{SCHEMA_NAME}}"
    And the response time should be under {{TIME_MS}}ms

  @API @ErrorHandling @TestId.{{TCID}}-API-002
  Scenario Outline: {{FEATURE_NAME}} API - Error scenarios
    When a {{METHOD}} request is sent with "<condition>"
    Then the response status should be <status_code>
    And the error message should contain "<error_fragment>"
    
    Examples:
      | condition | status_code | error_fragment |
      | missing_auth | 401 | Unauthorized |
      | invalid_payload | 400 | Bad Request |
      | rate_limit | 429 | Too Many Requests |

  # ============================================
  # END-TO-END USER JOURNEYS
  # ============================================
  
  @E2E @Critical @UserJourney @P0 @TestId.{{TCID}}-E2E-001
  Scenario: {{FEATURE_NAME}} - Complete user journey
    Given the user starts at the landing page
    When the user completes the full {{FEATURE}} flow
    Then the journey should complete successfully
    And all intermediate states should be correct
    And the final state should match expected outcome

  # ============================================
  # SECURITY TESTS
  # ============================================
  
  @Security @OWASP @Critical @TestId.{{TCID}}-SEC-001
  Scenario: {{FEATURE_NAME}} - SQL injection protection
    Given the user is on the {{FEATURE}} page
    When the user enters SQL injection payload "' OR '1'='1"
    And submits the form
    Then the application should not crash
    And no database error should be exposed
    And the attempt should be logged

  @Security @OWASP @XSS @TestId.{{TCID}}-SEC-002
  Scenario: {{FEATURE_NAME}} - XSS prevention
    When the user enters XSS payload "<script>alert('xss')</script>"
    Then the script should not execute
    And the input should be sanitized or encoded

  @Security @Authentication @TestId.{{TCID}}-SEC-003
  Scenario: {{FEATURE_NAME}} - Session fixation protection
    Given the user has an existing session
    When the user authenticates
    Then a new session ID should be generated
    And the old session should be invalidated

  # ============================================
  # ACCESSIBILITY TESTS
  # ============================================
  
  @Accessibility @WCAG2.1-AA @TestId.{{TCID}}-A11Y-001
  Scenario: {{FEATURE_NAME}} - Keyboard navigation
    Given the user is using only keyboard
    When the user navigates through the {{FEATURE}} flow
    Then all interactive elements should be reachable
    And the focus order should be logical
    And focus indicators should be visible

  @Accessibility @ScreenReader @TestId.{{TCID}}-A11Y-002
  Scenario: {{FEATURE_NAME}} - Screen reader compatibility
    Given the user is using a screen reader
    When the {{FEATURE}} page is loaded
    Then all form fields should have associated labels
    And error messages should be announced
    And status updates should be communicated

  # ============================================
  # EXPLORATORY / USABILITY TESTS
  # ============================================
  
  @Exploratory @Usability @TestId.{{TCID}}-EXP-001
  Scenario: {{FEATURE_NAME}} - Error message clarity
    When the user encounters an error condition
    Then the error message should be clear and actionable
    And it should suggest how to resolve the issue
    And it should not expose technical details

  @Exploratory @Usability @TestId.{{TCID}}-EXP-002
  Scenario: {{FEATURE_NAME}} - Recovery path availability
    When the user makes a mistake
    Then a clear recovery path should be available
    And previously entered valid data should be preserved
```

### 2. Mandatory Coverage Requirements

For EACH acceptance criterion, include:

| Test Category | Minimum Count | Tag Pattern |
|---------------|---------------|-------------|
| Smoke | 1 | `@Smoke.Critical` |
| Sanity | 1-2 | `@Sanity.High` |
| Functional Positive | 2-3 | `@Functional.Positive` |
| Functional Negative | 2-4 | `@Functional.Negative` |
| Boundary Value | 4-6 | `@Boundary` |
| Data-Driven | 1 with 3+ examples | `@DataDriven` |
| API Contract | 2 | `@API.Contract` |
| API Error Handling | 2-3 | `@API.Error` |
| E2E Journey | 1 | `@E2E.Critical` |
| Security (OWASP) | 2-3 | `@Security.OWASP` |
| Accessibility | 1-2 | `@Accessibility` |
| Exploratory | 1 | `@Exploratory` |

### 3. BDD Writing Standards

#### Step Patterns

| Intent | Pattern | Example |
|--------|---------|---------|
| Navigation | `Given I am on the "{page}" page` | Given I am on the "login" page |
| State Setup | `Given the {entity} has {attribute}` | Given the user has a verified email |
| Action | `When I {action} the {element}` | When I click the "Submit" button |
| Form Input | `When I enter "{value}" into the "{field}" field` | When I enter "john@test.com" into the "email" field |
| API Call | `When I send a {method} request to "{endpoint}"` | When I send a POST request to "/api/login" |
| Verification | `Then I should see "{text}"` | Then I should see "Welcome back" |
| State Check | `Then the {entity} should have {state}` | Then the user should be authenticated |
| Data Check | `Then the {field} should contain "{value}"` | Then the error message should contain "Invalid" |

#### Step Best Practices
1. **One action per step** - Split compound actions
2. **Use quotes for variable data** - `"username"` not `username`
3. **Be specific with locators** - `"Submit" button` not `button`
4. **Include state in Then steps** - Don't just check UI, verify data
5. **Use data tables for complex input** - Not multiple And steps

### 4. Test ID Convention

```
Format: TC-{MODULE}-{TYPE}-{SEQUENCE}

Examples:
- TC-AUTH-SMOKE-001      (Authentication smoke test)
- TC-CKOUT-API-003       (Checkout API test)
- TC-PYMT-E2E-001        (Payment E2E journey)
- TC-USER-BND-002        (User management boundary test)
- TC-INV-SEC-001         (Inventory security test)

Type Codes:
- SMOKE - Smoke tests
- SANITY - Sanity tests
- FUNC - Functional tests
- BND - Boundary value tests
- DD - Data-driven tests
- API - API/Integration tests
- E2E - End-to-end tests
- SEC - Security tests
- PERF - Performance tests
- A11Y - Accessibility tests
- EXP - Exploratory tests
```

## INTELLIGENT CLARIFICATION ENGINE

### Auto-Trigger Questions

Ask for clarification when ANY of these are missing:

#### 🔴 Critical (Must Have)
```markdown
❓ MISSING: Feature Name
   → "What is the name of the feature to test?"

❓ MISSING: Application Type  
   → "What type of application is this? (Web/Mobile/API/Desktop)"

❓ MISSING: User Story or Acceptance Criteria
   → "Please provide the user story or at least 2-3 acceptance criteria for this feature."
```

#### 🟡 Important (High Impact on Quality)
```markdown
❓ MISSING: User Roles
   → "What different user roles interact with this feature? (e.g., Admin, Customer, Guest)"

❓ MISSING: Business Rules
   → "Are there specific validation rules or business constraints I should know about?"

❓ MISSING: Integration Points
   → "Does this feature integrate with external services (Email, Payment, SMS, etc.)?"
```

#### 🟢 Enhancing (Improves Specificity)
```markdown
❓ MISSING: Tech Stack
   → "What technology stack is used? This helps me write relevant API and integration tests."

❓ MISSING: Performance Requirements
   → "Are there specific response time or throughput requirements?"

❓ MISSING: Compliance Requirements
   → "Are there regulatory requirements (GDPR, HIPAA, PCI-DSS) that need testing?"
```

### Smart Default Configuration

If user provides minimal input, ask these configuration questions:

```markdown
## Configuration Options

### 1. Test Coverage Level
   - [ ] Essential (Smoke + Critical path only)
   - [ ] Standard (All functional + API + E2E)
   - [ ] Comprehensive (Standard + Security + Performance + Accessibility)

### 2. BDD Verbosity
   - [ ] Concise (Minimal steps, implicit context)
   - [ ] Standard (Clear Given/When/Then separation)
   - [ ] Verbose (Explicit data setup, detailed assertions)

### 3. Automation Target
   - [ ] Playwright (JavaScript/TypeScript)
   - [ ] Cypress
   - [ ] Selenium (Java/Python/C#)
   - [ ] Robot Framework
   - [ ] Cucumber (JVM/JavaScript/Ruby)
   - [ ] API-only (REST Assured, Postman, pytest)

### 4. Data-Driven Approach
   - [ ] Inline (Examples table in feature file)
   - [ ] External CSV/JSON
   - [ ] Database-driven
   - [ ] Dynamic/Faker-generated
```

## OUTPUT FORMATS

### Primary: Gherkin Feature File
```gherkin
@Feature.Authentication @Sprint.23 @Owner.SDET_Team
Feature: User Login and Authentication
  As a registered user
  I want to securely log into the application
  So that I can access my personalized dashboard

  Background:
    Given the authentication service is available
    And the test database contains the following users:
      | email | password | role | status |
      | admin@test.com | Admin123! | admin | active |
      | user@test.com | User123! | customer | active |
      | locked@test.com | Locked123! | customer | locked |

  @Smoke.Critical @P0 @CI_Gate @TestId.TC-AUTH-SMOKE-001
  Scenario: Admin user can successfully log in
    Given the user navigates to "/login"
    When the user enters "admin@test.com" into the "email" field
    And the user enters "Admin123!" into the "password" field
    And the user clicks the "Sign In" button
    Then the user should be redirected to "/admin/dashboard"
    And the page should display "Welcome, Admin"

  @Functional.DataDriven @P1 @Regression @TestId.TC-AUTH-FUNC-DD-001
  Scenario Outline: Login with various credential combinations
    Given the user is on the login page
    When the user enters "<email>" into the "email" field
    And the user enters "<password>" into the "password" field
    And the user clicks the "Sign In" button
    Then the user should see "<expected_message>"
    And the URL should be "<expected_url>"

    Examples:
      | email | password | expected_message | expected_url |
      | user@test.com | User123! | Welcome back | /dashboard |
      | user@test.com | WrongPass! | Invalid credentials | /login |
      | locked@test.com | Locked123! | Account locked | /login |
      | notfound@test.com | AnyPass123! | Invalid credentials | /login |
      | invalid-email | AnyPass123! | Please enter a valid email | /login |

  @Boundary @Validation @TestId.TC-AUTH-BND-001
  Scenario Outline: Password length boundary validation
    When the user enters "user@test.com" into the "email" field
    And the user enters "<password>" into the "password" field
    Then the field validation should be "<result>"

    Examples:
      | password | length | result |
      | Short1! | 7 | too_short |
      | Valid123! | 8 | valid |
      | A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0 | 40 | valid |
      | A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0U | 41 | too_long |

  @API.Contract @Integration @TestId.TC-AUTH-API-001
  Scenario: Login API returns valid JWT token
    Given the API base URL is configured
    And the Content-Type header is "application/json"
    When a POST request is sent to "/api/v1/auth/login" with body:
      """
      {
        "email": "user@test.com",
        "password": "User123!"
      }
      """
    Then the response status code should be 200
    And the response should contain a valid JWT token
    And the token "exp" claim should be 3600 seconds from now
    And the response schema should match "auth-success-schema.json"

  @Security.OWASP.Injection @Critical @TestId.TC-AUTH-SEC-001
  Scenario: Login is protected against SQL injection
    When the user enters "' OR '1'='1" into the "email" field
    And the user enters "' OR '1'='1" into the "password" field
    And the user clicks the "Sign In" button
    Then the login should fail
    And the error message should not contain SQL keywords
    And no stack trace should be visible
    And the security event should be logged

  @E2E.Critical @UserJourney @TestId.TC-AUTH-E2E-001
  Scenario: Complete login to profile update journey
    Given the user is on the home page
    When the user clicks "Sign In"
    And completes login with valid credentials
    And navigates to "My Profile"
    And updates the profile information
    And saves the changes
    Then the profile should be updated successfully
    And a success notification should appear
    And the changes should persist after logout and login
```

### Secondary: JSON Format (For Tool Integration)
```json
{
  "test_cases": [
    {
      "id": "TC-AUTH-SMOKE-001",
      "tags": ["@Smoke", "@Critical", "@P0"],
      "feature": "User Authentication",
      "scenario": "Admin user can successfully log in",
      "type": "smoke",
      "priority": "P0",
      "bdd": {
        "given": [
          "the user navigates to \"/login\""
        ],
        "when": [
          "the user enters \"admin@test.com\" into the \"email\" field",
          "the user enters \"Admin123!\" into the \"password\" field",
          "the user clicks the \"Sign In\" button"
        ],
        "then": [
          "the user should be redirected to \"/admin/dashboard\"",
          "the page should display \"Welcome, Admin\""
        ]
      },
      "automation": {
        "framework": "playwright",
        "parallelizable": true,
        "estimated_duration_ms": 5000
      },
      "data_requirements": {
        "test_accounts": ["admin@test.com"],
        "database_state": "seeded"
      }
    }
  ]
}
```

### Tertiary: CSV Format (For Test Management Tools)

| Test ID | Tags | Feature | Scenario | Preconditions | Steps | Expected Results | Priority | Automated | Data-Driven |
|---------|------|---------|----------|---------------|-------|------------------|----------|-----------|-------------|
| TC-AUTH-SMOKE-001 | @Smoke @Critical @P0 | Authentication | Admin user login | App running, test account exists | 1. Navigate to /login<br>2. Enter valid credentials<br>3. Click Sign In | Redirect to dashboard | P0 | Yes | No |
| TC-AUTH-FUNC-DD-001 | @Functional @DataDriven | Authentication | Login variations | App running | Enter various credential combinations | Appropriate messages per data row | P1 | Yes | Yes |

---

## 🏷️ Comprehensive Tagging System

### Tag Taxonomy

```
@Category.SubCategory.Attribute.Modifier

Categories:
├── @Smoke          - Build verification
├── @Sanity         - Quick regression
├── @Regression     - Full test suite
├── @Functional     - Feature testing
├── @API            - Service layer
├── @E2E            - End-to-end flows
├── @Security       - OWASP, compliance
├── @Performance    - Speed, load, stress
├── @Accessibility  - WCAG compliance
├── @Exploratory    - UX, edge cases
└── @DataDriven     - Parameterized

SubCategories (Examples):
├── @Functional.Positive
├── @Functional.Negative
├── @Functional.Boundary
├── @API.Contract
├── @API.Integration
├── @API.ErrorHandling
├── @Security.OWASP
├── @Security.Authentication
├── @Security.Authorization
└── @Performance.Load

Attributes:
├── @Critical, @High, @Medium, @Low (Priority)
├── @P0, @P1, @P2, @P3 (Severity)
├── @CI_Gate (Include in CI/CD)
├── @Nightly (Nightly run)
├── @Manual (Manual only)
├── @Flaky (Known instability)
└── @Skip (Temporarily disabled)

Modifiers:
├── @Parallel.Safe
├── @Parallel.Unsafe
├── @Retry.3
├── @Timeout.30s
└── @Browser.Chrome, @Browser.Firefox
```

### Tag Usage Examples

```gherkin
# Critical smoke test for CI gate
@Smoke.Critical @P0 @CI_Gate @Browser.Chrome @Parallel.Safe

# API contract test
@API.Contract @Integration @P1 @Retry.3

# Data-driven security test
@Security.OWASP.Injection @DataDriven @P1

# E2E journey with specific browser requirement
@E2E.Critical @UserJourney @Browser.Chrome @Parallel.Unsafe

# Accessibility test with WCAG standard
@Accessibility.WCAG2.1-AA @ScreenReader @P2

# Performance baseline test
@Performance.Baseline @Load.1000Users @Timeout.5m
```

---

## 📊 Data-Driven Testing Patterns

### Pattern 1: Equivalence Partitioning

```gherkin
@DataDriven @Equivalence @Validation
Scenario Outline: Email validation with equivalence partitions
  When the user enters "<email>" into the email field
  Then the validation result should be "<result>"
  And the error type should be "<error_type>"

  Examples:
    # Valid partition
    | email | result | error_type |
    | user@domain.com | valid | none |
    | user.name@domain.co.uk | valid | none |
    
    # Invalid format partition  
    | invalid-email | invalid | format_error |
    | @domain.com | invalid | missing_local |
    | user@ | invalid | missing_domain |
    
    # Empty/null partition
    | | invalid | required |
    | null | invalid | required |
```

### Pattern 2: Decision Table

```gherkin
@DataDriven @DecisionTable @BusinessRules
Scenario Outline: Checkout eligibility based on multiple conditions
  Given the user is "<user_type>"
  And the cart total is "<cart_total>"
  And the shipping address is "<address_status>"
  When the user attempts to checkout
  Then checkout should be "<checkout_result>"
  And the message should be "<message>"

  Examples:
    | user_type | cart_total | address_status | checkout_result | message |
    | logged_in | > $25 | verified | allowed | Proceed to payment |
    | logged_in | < $25 | verified | allowed | Proceed to payment |
    | guest | > $25 | new | allowed | Create account or guest checkout |
    | guest | < $25 | new | blocked | Minimum order $25 |
    | logged_in | any | unverified | blocked | Please verify address |
```

### Pattern 3: State Transition

```gherkin
@DataDriven @StateMachine @OrderLifecycle
Scenario Outline: Order status transitions
  Given the order is in "<current_status>" status
  When "<action>" is performed
  Then the order status should be "<new_status>"
  And "<notification>" should be sent

  Examples:
    | current_status | action | new_status | notification |
    | pending | payment_received | confirmed | order_confirmation |
    | pending | payment_failed | cancelled | payment_failed |
    | confirmed | ship | shipped | shipping_notification |
    | shipped | deliver | delivered | delivery_confirmation |
    | delivered | return_request | return_pending | return_instructions |
```

### Pattern 4: Pairwise Testing

```gherkin
@DataDriven @Pairwise @Configuration
Scenario Outline: Cross-browser form submission
  Given the user is using "<browser>" on "<os>"
  And the viewport is "<viewport>"
  When the user submits the registration form
  Then the submission should "<result>"

  # Optimized with pairwise algorithm to reduce from 27 to 9 combinations
  Examples:
    | browser | os | viewport | result |
    | Chrome | Windows | desktop | succeed |
    | Chrome | Mac | mobile | succeed |
    | Chrome | Linux | tablet | succeed |
    | Firefox | Windows | tablet | succeed |
    | Firefox | Mac | desktop | succeed |
    | Firefox | Linux | mobile | succeed |
    | Safari | Windows | mobile | succeed |
    | Safari | Mac | tablet | succeed |
    | Safari | Linux | desktop | succeed |
```

---

## 🔐 Domain-Specific Scenario Library

### E-Commerce Scenarios

```gherkin
@ECommerce @Cart @Inventory
Feature: Shopping Cart Management

  @Smoke @Critical @TestId.TC-CART-SMOKE-001
  Scenario: Add item to cart
    Given the user is browsing products
    When the user clicks "Add to Cart" on "Wireless Headphones"
    Then the cart count should show "1"
    And "Wireless Headphones" should appear in the cart
    And the price should be "$99.99"

  @Boundary @Inventory @TestId.TC-CART-BND-001
  Scenario Outline: Add items up to stock limit
    Given "Limited Edition Watch" has "<available_stock>" items in stock
    When the user tries to add "<quantity>" items to cart
    Then the result should be "<result>"
    And the message should be "<message>"

    Examples:
      | available_stock | quantity | result | message |
      | 10 | 10 | success | Added to cart |
      | 10 | 11 | failure | Only 10 items available |
      | 1 | 1 | success | Added to cart |
      | 0 | 1 | failure | Out of stock |

  @E2E @Checkout @Payment.Stripe @TestId.TC-CART-E2E-001
  Scenario: Complete purchase with cart items
    Given the user has items in cart
    And the user is logged in
    When the user proceeds to checkout
    And enters valid shipping address
    And enters valid Stripe test card "4242 4242 4242 4242"
    And confirms the purchase
    Then the order should be created
    And inventory should be reduced
    And confirmation email should be sent
```

### Healthcare Scenarios

```gherkin
@Healthcare @HIPAA @PHI
Feature: Patient Record Access

  @Security @HIPAA @Audit @Critical @TestId.TC-HIPAA-SEC-001
  Scenario: Unauthorized PHI access is blocked and logged
    Given Dr. Smith is logged in
    And Dr. Smith is NOT assigned to patient "John Doe"
    When Dr. Smith attempts to view patient "John Doe" records
    Then access should be denied
    And an audit log entry should be created with:
      | field | value |
      | user_id | dr.smith@hospital.com |
      | action | PHI_ACCESS_DENIED |
      | patient_id | ***REDACTED*** |
      | timestamp | <current_time> |
      | ip_address | <client_ip> |
    And security team should be notified

  @Audit @Consent @TestId.TC-HIPAA-AUD-001
  Scenario: Patient consent is verified before data sharing
    Given patient "Jane Doe" has opted out of research data sharing
    When a research export is initiated
    Then Jane Doe's records should be excluded
    And an exclusion log should note "Consent opted out"
```

### Finance/Banking Scenarios

```gherkin
@Finance @Banking @Transaction
Feature: Fund Transfer

  @Security.Idempotency @Critical @TestId.TC-FIN-SEC-001
  Scenario: Duplicate transfer request is idempotent
    Given account "A123" has balance "$1000"
    And account "B456" has balance "$500"
    When a transfer of "$100" from "A123" to "B456" is initiated
    And the same transfer is retried with same idempotency key
    Then only one transfer should be recorded
    And account "A123" balance should be "$900"
    And account "B456" balance should be "$600"
    And both requests should receive identical response

  @BusinessRule @Limit @TestId.TC-FIN-BR-001
  Scenario Outline: Transfer limits enforcement
    Given the user has daily limit of "$5000"
    And today's transferred amount is "$<already_transferred>"
    When the user attempts to transfer "$<new_amount>"
    Then the transfer should be "<result>"

    Examples:
      | already_transferred | new_amount | result |
      | 0 | 5000 | approved |
      | 4000 | 1000 | approved |
      | 4000 | 1001 | declined |
      | 5000 | 1 | declined |
```

---

## 🤖 Automation Framework Mappings

### Playwright Mapping

```gherkin
# Given steps
Given the user navigates to "{page}"           → page.goto(url)
Given the user is logged in as "{role}"         → auth.login(role)

# When steps  
When the user clicks "{element}"                → page.click(selector)
When the user enters "{value}" into "{field}"   → page.fill(selector, value)
When the user selects "{option}" from "{dropdown}" → page.selectOption(selector, option)

# Then steps
Then the user should see "{text}"               → expect(page).toHaveText(text)
Then the URL should be "{path}"                 → expect(page).toHaveURL(path)
Then the element "{selector}" should be visible → expect(selector).toBeVisible()
```

### Cypress Mapping

```gherkin
# Given steps
Given the user visits "{page}"                  → cy.visit(url)
Given the user is authenticated                 → cy.login()

# When steps
When the user clicks "{element}"                → cy.get(selector).click()
When the user types "{value}" into "{field}"    → cy.get(selector).type(value)

# Then steps
Then the page should contain "{text}"           → cy.contains(text)
Then the URL should include "{path}"            → cy.url().should('include', path)
```

### REST Assured (API) Mapping

```gherkin
# Given steps
Given the API base URL is set                   → RestAssured.baseURI = url
Given the authentication token is valid         → header("Authorization", token)

# When steps
When a GET request is sent to "{endpoint}"      → given().get(endpoint)
When a POST request is sent with body           → given().body(payload).post(endpoint)

# Then steps
Then the response status should be {code}       → .then().statusCode(code)
Then the response should contain field "{path}" → .body(path, equalTo(value))
```

---

## ✅ Quality Checklist

### Pre-Generation
- [ ] Feature name is descriptive
- [ ] User story follows "As a... I want... So that..." format
- [ ] At least 2 acceptance criteria provided
- [ ] Application type is specified

### Post-Generation
- [ ] All acceptance criteria have corresponding test cases
- [ ] Every positive scenario has negative counterpart(s)
- [ ] Smoke tests cover critical path
- [ ] Data-driven tests include boundary values
- [ ] API tests include contract validation
- [ ] Security tests cover OWASP Top 10 risks
- [ ] Tags follow consistent naming convention
- [ ] Test IDs are unique and sequential
- [ ] Background is used for common preconditions
- [ ] Steps are atomic and reusable

### Automation Readiness
- [ ] All UI elements have clear locator descriptions
- [ ] API tests include status code assertions
- [ ] Data variations are clearly specified
- [ ] Test data setup is documented
- [ ] No hard-coded values in scenarios (use Examples)
- [ ] Parallel execution considerations noted in tags

---

## 📈 Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | 2024-03 | Complete rewrite with BDD-first approach, intelligent clarification engine, comprehensive tagging system, data-driven patterns |
| 2.1 | 2024-01 | Added security and accessibility templates |
| 2.0 | 2023-12 | Added API testing and automation mappings |
| 1.0 | 2023-10 | Initial version |

---

> **💡 Pro Tip:** Use `@CI_Gate` tag for tests that must pass before merging code. Keep this set small and fast (< 5 minutes total execution).
