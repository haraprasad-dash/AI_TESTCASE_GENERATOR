# 🎯 Test Plan Generation Skill (Enterprise Grade)

> **Version:** 2.0 | **Framework:** BDD-First | **Compatible:** Groq, Ollama, OpenAI, Claude
> 
> Generate comprehensive, automation-ready test plans with intelligent clarification loops.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Master Prompt Template](#master-prompt-template)
3. [BDD Test Plan Structure](#bdd-test-plan-structure)
4. [Test Types & Tagging Standards](#test-types--tagging-standards)
5. [Data-Driven Test Planning](#data-driven-test-planning)
6. [Clarification Framework](#clarification-framework)
7. [Domain-Specific Templates](#domain-specific-templates)
8. [Output Formats](#output-formats)
9. [Quality Gates](#quality-gates)

---

## 🚀 Quick Start

### Minimum Required Input
```yaml
project_name: "E-Commerce Platform"
application_type: "Web"  # Web | Mobile | API | Desktop
features:
  - User Authentication
  - Product Search
  - Checkout Flow
timeline: "2 weeks"
team_size: 3
```

### One-Line Command
```text
Generate a BDD-based test plan for [PROJECT] covering functional, API, smoke, 
sanity, negative, and E2E scenarios with proper tagging for automation.
```

---

## 🎨 Master Prompt Template

```markdown
# ROLE: Principal SDET & Test Architect

## MISSION
Generate a comprehensive, BDD-formatted test plan that is directly usable for 
both manual execution and test automation framework implementation.

## INPUT CONTEXT
```yaml
Project: {{PROJECT_NAME}}
Application Type: {{APP_TYPE}}  # Web/Mobile/API/Desktop/Hybrid
Domain: {{DOMAIN}}  # E-commerce/Healthcare/Finance/SaaS/etc.
Release Version: {{VERSION}}
Sprint/Iteration: {{SPRINT}}

Features in Scope:
{{FEATURES_LIST}}

Features Out of Scope:
{{OUT_OF_SCOPE}}

Tech Stack:
  Frontend: {{FRONTEND_TECH}}
  Backend: {{BACKEND_TECH}}
  Database: {{DATABASE}}
  APIs: {{API_TYPE}}  # REST/GraphQL/gRPC/SOAP
  Mobile: {{MOBILE_PLATFORM}}  # iOS/Android/Both
  
Team Structure:
  - QA Lead: {{LEAD_COUNT}}
  - QA Engineers: {{QA_COUNT}}
  - Automation Engineers: {{AUTO_COUNT}}
  
Timeline:
  Start Date: {{START_DATE}}
  End Date: {{END_DATE}}
  Working Days: {{DAYS}}

Environments:
  - Development: {{DEV_URL}}
  - Staging: {{STAGING_URL}}
  - Production: {{PROD_URL}}

Compliance Requirements:
{{COMPLIANCE}}  # GDPR/HIPAA/SOC2/PCI-DSS/etc.

Special Considerations:
{{SPECIAL_NOTES}}  # Multi-tenancy, i18n, accessibility, etc.
```

## OUTPUT REQUIREMENTS

### 1. Test Plan Document Structure (IEEE 829 + BDD Enhanced)

```
# Test Plan: {{PROJECT_NAME}} v{{VERSION}}

## 1. Executive Summary
   - Project overview
   - Testing objectives
   - Success criteria
   - Risk summary

## 2. Scope Definition
   ### 2.1 In Scope
   - Features to be tested
   - Test types included
   
   ### 2.2 Out of Scope
   - Explicitly excluded features
   - Deferred test types
   
   ### 2.3 Assumptions & Dependencies

## 3. Test Strategy
   ### 3.1 Test Levels
   | Level | Description | Coverage Target | Tools |
   |-------|-------------|-----------------|-------|
   
   ### 3.2 Test Types Matrix
   | Type | Strategy | Automation % | Tags |
   |------|----------|--------------|------|
   
   ### 3.3 BDD Approach
   - Feature file structure
   - Step definition strategy
   - Scenario outline usage for data-driven tests

## 4. Test Environment
   ### 4.1 Hardware Requirements
   ### 4.2 Software Stack
   ### 4.3 Test Data Strategy
   ### 4.4 Environment Configuration Matrix

## 5. Test Case Inventory (BDD Format)
   
   ### 5.1 Feature: [Feature Name]
   
   #### Scenario Categories:
   
   ##### @Smoke @Critical
   ```gherkin
   Feature: User Login
     @Smoke @Critical @Authentication @Functional
     Scenario: Successful login with valid credentials
       Given the user is on the login page
       When the user enters valid username "valid_user"
       And the user enters valid password "valid_pass"
       And the user clicks the login button
       Then the user should be redirected to the dashboard
       And the user session should be established
   ```
   
   ##### @Sanity @Regression
   ```gherkin
     @Sanity @Regression @Authentication @Functional
     Scenario Outline: Login validation with various credentials
       Given the user is on the login page
       When the user enters username "<username>"
       And the user enters password "<password>"
       And the user clicks the login button
       Then the user should see "<expected_result>"
       
       Examples:
         | username    | password    | expected_result              |
         | valid_user  | valid_pass  | Dashboard page               |
         | valid_user  | wrong_pass  | Invalid credentials message  |
         | locked_user | valid_pass  | Account locked message       |
         | empty       | empty       | Required fields validation   |
   ```
   
   ##### @Negative @Validation
   ```gherkin
     @Negative @Validation @Authentication @Security
     Scenario: Login with SQL injection attempt
       Given the user is on the login page
       When the user enters username "' OR '1'='1"
       And the user enters password "' OR '1'='1"
       And the user clicks the login button
       Then the login should fail
       And no database error should be exposed
       And the attempt should be logged in security logs
   ```
   
   ##### @API @Integration
   ```gherkin
     @API @Integration @Authentication @Postman @Contract
     Scenario: Login API returns valid JWT token
       Given the API endpoint "/api/v1/auth/login" is available
       When a POST request is sent with valid credentials
       Then the response status should be 200
       And the response should contain a valid JWT token
       And the token should expire in 3600 seconds
       And the response schema should match the contract
   ```
   
   ##### @E2E @Critical
   ```gherkin
     @E2E @Critical @UserJourney @Checkout @Payment
     Scenario: Complete purchase flow from login to order confirmation
       Given the user is logged in
       And the user has items in cart
       When the user proceeds to checkout
       And enters valid shipping details
       And enters valid payment information
       And confirms the order
       Then the order should be created successfully
       And the user should receive order confirmation
       And the inventory should be updated
       And the payment should be processed
   ```
   
   ##### @Exploratory @Usability
   ```gherkin
     @Exploratory @Usability @Accessibility @WCAG
     Scenario: Login page accessibility check
       Given the user is using a screen reader
       When the user navigates to the login page
       Then all form fields should have proper labels
       And the focus order should be logical
       And error messages should be announced
   ```

## 6. Automation Strategy
   ### 6.1 Framework Selection
   ### 6.2 CI/CD Integration
   ### 6.3 Parallel Execution Plan
   ### 6.4 Reporting & Metrics

## 7. Entry & Exit Criteria
   ### 7.1 Entry Criteria (Definition of Ready)
   ### 7.2 Exit Criteria (Definition of Done)
   ### 7.3 Suspension & Resumption Criteria

## 8. Risk Assessment & Mitigation
   | Risk | Impact | Probability | Mitigation Strategy |

## 9. Resource Planning
   ### 9.1 Team Roles & Responsibilities
   ### 9.2 Training Requirements
   ### 9.3 Tool Licensing

## 10. Schedule & Milestones
    ### 10.1 Test Execution Phases
    ### 10.2 Deliverables Timeline
    ### 10.3 Critical Path

## 11. Deliverables
    | Deliverable | Format | Owner | Due Date |

## 12. Appendices
    ### 12.1 Tagging Standards
    ### 12.2 Naming Conventions
    ### 12.3 Test Data Requirements
```

### 2. Mandatory Test Coverage Areas

For EACH feature, generate scenarios for:

| Category | Tag | Count | Description |
|----------|-----|-------|-------------|
| Smoke Tests | @Smoke | 2-3 | Critical path validation |
| Sanity Tests | @Sanity | 3-5 | Build verification |
| Functional Positive | @Functional @Positive | 5-10 | Happy path scenarios |
| Functional Negative | @Functional @Negative | 5-10 | Error handling, validation |
| Boundary Value | @Boundary | 3-5 | Min/max/limit testing |
| API Tests | @API | 4-8 | Contract, integration, error codes |
| End-to-End | @E2E | 2-4 | User journey flows |
| Security Tests | @Security | 2-4 | Auth, injection, XSS |
| Performance Baseline | @Performance | 1-2 | Response time, load |
| Accessibility | @Accessibility | 1-2 | WCAG compliance |
| Exploratory | @Exploratory | 2-3 | Usability, edge cases |
| Data-Driven | @DataDriven | 3-5 | Parameterized scenarios |

### 3. BDD Writing Standards

#### Gherkin Syntax Rules
- Use `Given` for preconditions and context setup
- Use `When` for actions (single action per step preferred)
- Use `Then` for verifications (assertions)
- Use `And`/`But` to extend any of the above
- Use `Background` for common preconditions
- Use `Scenario Outline` + `Examples` for data-driven tests

#### Tag Hierarchy
```
@SuiteType.Criticality.Component.Feature.SubFeature

Examples:
@Smoke.Critical.Authentication.Login.Positive
@Regression.High.Checkout.Payment.Stripe
@API.Medium.Inventory.Stock.Update
```

### 4. Data-Driven Test Requirements

Every data-driven scenario MUST include:
- At least 3 data variations in Examples table
- Edge cases (null, empty, max length, special chars)
- Valid boundary values
- Invalid boundary values
- Different user roles/permissions (if applicable)

### 5. API Test Specifications

For each API endpoint, include:
```gherkin
@API @Contract @{{METHOD}} @{{ENDPOINT_TAG}}
Scenario Outline: {{ENDPOINT}} - {{DESCRIPTION}}
  Given the API base URL is set
  And the authentication token is "<auth_type>"
  When a {{METHOD}} request is sent to "{{ENDPOINT}}"
  And the request body is:
    """
    <request_body>
    """
  Then the response status code should be <status_code>
  And the response should match schema "<schema_name>"
  And the response time should be less than <max_ms>ms
  And the response header "<header>" should be "<value>"
  
  Examples:
    | description | auth_type | request_body | status_code | schema_name | max_ms |
```

### 6. Quality Checklist

Before finalizing, verify:
- [ ] All features have at least one @Smoke test
- [ ] Every positive scenario has corresponding negative scenarios
- [ ] All API endpoints have contract tests
- [ ] Data-driven tests cover boundary values
- [ ] Tags follow the hierarchical naming convention
- [ ] E2E scenarios cover critical user journeys
- [ ] Security scenarios cover OWASP Top 10 risks
- [ ] Accessibility tests cover WCAG 2.1 AA standards
- [ ] Test IDs are unique and follow naming convention
- [ ] Preconditions are clear and testable

## INTELLIGENT CLARIFICATION

If any of the following are missing or unclear, ask specific questions:

1. **Missing Domain Context**: "What industry/domain does this application serve? (e.g., Healthcare, Finance, E-commerce)"
2. **Unclear Compliance**: "Are there any regulatory requirements (GDPR, HIPAA, PCI-DSS) that affect testing?"
3. **Incomplete User Roles**: "What are the different user roles/personas? (e.g., Admin, Customer, Guest, Premium)"
4. **Missing Integration Points**: "What third-party integrations exist? (Payment gateways, SMS, Email, Analytics)"
5. **Unclear Scale**: "What is the expected user load/concurrency for performance testing?"
6. **Missing Data Strategy**: "What are the data privacy requirements for test data?"

Generate the test plan now with the highest quality standards.
```

---

## 🏷️ Test Types & Tagging Standards

### Standard Tag Library

#### By Test Suite Type
| Tag | Description | When to Use |
|-----|-------------|-------------|
| `@Smoke` | Critical path only | Build verification, CI/CD gate |
| `@Sanity` | Core functionality | Pre-release validation |
| `@Regression` | Existing features | Full test cycles |
| `@Functional` | Feature testing | Sprint testing |

#### By Criticality
| Tag | SLA | Example |
|-----|-----|---------|
| `@Critical` | P0 - Must pass | Payment processing |
| `@High` | P1 - Should pass | User registration |
| `@Medium` | P2 - Good to have | Profile updates |
| `@Low` | P3 - Nice to have | UI polish |

#### By Test Type
| Tag | Automation | Framework |
|-----|------------|-----------|
| `@API` | Full | REST Assured, Postman |
| `@E2E` | Full | Playwright, Selenium, Cypress |
| `@Unit` | N/A | Jest, JUnit, pytest |
| `@Integration` | Full | TestContainers, WireMock |
| `@Contract` | Full | Pact, Spring Cloud Contract |

#### By Testing Focus
| Tag | Focus Area |
|-----|------------|
| `@Security` | Auth, injection, XSS, CSRF |
| `@Performance` | Load, stress, soak |
| `@Accessibility` | WCAG, screen readers |
| `@Usability` | UX, navigation |
| `@Localization` | i18n, l10n |
| `@Compatibility` | Cross-browser, devices |

#### By Data Strategy
| Tag | Description |
|-----|-------------|
| `@DataDriven` | Uses Scenario Outline |
| `@Positive` | Happy path |
| `@Negative` | Error cases |
| `@Boundary` | Limit testing |

### Tag Combination Examples

```gherkin
# Critical smoke test for CI/CD gate
@Smoke.Critical.Authentication.Login @CI_Gate

# Data-driven API test with security focus
@API.High.Authentication.Login @Security @DataDriven @Contract

# Full E2E user journey
@E2E.Critical.Checkout.Complete @UserJourney @Payment @Stripe

# Accessibility-focused exploratory test
@Exploratory.Medium.UI.Navigation @Accessibility @WCAG2.1-AA

# Performance baseline test
@Performance.Medium.API.ResponseTime @Baseline @Load.Under1000Users
```

---

## 💾 Data-Driven Test Planning

### Data Source Patterns

#### 1. Inline Examples (Small datasets)
```gherkin
Scenario Outline: User registration with various inputs
  When the user registers with email "<email>" and password "<password>"
  Then the result should be "<result>"
  
  Examples:
    | email | password | result |
    | valid@test.com | Pass123! | success |
    | invalid-email | Pass123! | invalid_email_error |
    | valid@test.com | short | password_too_short |
```

#### 2. External Data Reference (Large datasets)
```gherkin
@ExternalData="test_data/registration.csv"
Scenario Outline: Bulk user registration tests
  When the user registers with data from row <row_id>
  Then the validation result should match expected
```

#### 3. Dynamic Data Generation
```gherkin
@DynamicData @Faker
Scenario: Create user with random valid data
  When the user registers with randomly generated valid data
  Then the registration should succeed
  And the user should receive confirmation email
```

### Test Data Categories to Include

| Category | Examples | Use Case |
|----------|----------|----------|
| Valid Data | Standard inputs | Positive testing |
| Invalid Format | Wrong type, malformed | Validation testing |
| Boundary Values | Min-1, Min, Max, Max+1 | Limit testing |
| Special Characters | Unicode, Emoji, HTML | Input sanitization |
| SQL Injection | `' OR 1=1 --` | Security testing |
| XSS Payloads | `<script>alert('xss')</script>` | Security testing |
| Large Payloads | 10MB strings | Stress testing |
| Null/Empty | null, "", [] | Null handling |
| Concurrent Data | Same resource, multiple users | Race condition testing |

---

## ❓ Clarification Framework

### Automatic Clarification Triggers

The AI should ask for clarification when:

#### 🔴 Blockers (Cannot proceed without)
1. **No application type specified**
   - "Is this a Web, Mobile, API, or Desktop application?"

2. **No domain context**
   - "What industry does this application belong to? (Healthcare, Finance, E-commerce, etc.)"

3. **Zero features specified**
   - "Please provide at least one feature to test."

#### 🟡 High Impact (Significantly affects quality)
4. **No user roles defined**
   - "What are the different user types? (e.g., Admin, Customer, Guest, Premium User)"

5. **No compliance mentioned**
   - "Are there regulatory requirements? (GDPR, HIPAA, PCI-DSS, SOC2)"

6. **No integration points**
   - "What third-party services does this application use? (Payment, Email, SMS, Analytics)"

#### 🟢 Nice to Have (Improves specificity)
7. **No performance criteria**
   - "What are the expected response times and concurrent user limits?"

8. **No browser/device requirements**
   - "Which browsers/versions and devices should be tested?"

### Smart Default Questions

If the user provides minimal input, ask these smart defaults:

```markdown
## Clarification Required

To generate the highest quality test plan, please answer:

### 1. BDD Strictness Level
   - [ ] Strict (Pure Given/When/Then, no technical details)
   - [ ] Moderate (Some technical context allowed)
   - [ ] Flexible (Implementation details in steps acceptable)

### 2. Test ID Format Preference
   - [ ] TC-FEATURE-001 (e.g., TC-AUTH-001)
   - [ ] MODULE_FEATURE_001 (e.g., AUTH_LOGIN_001)
   - [ ] Custom: _______

### 3. Automation Framework
   - [ ] Playwright (Recommended for Web)
   - [ ] Cypress
   - [ ] Selenium
   - [ ] Robot Framework
   - [ ] Custom: _______

### 4. Priority Test Types (Select top 3)
   - [ ] Functional (Happy path + edge cases)
   - [ ] API Contract testing
   - [ ] End-to-End user journeys
   - [ ] Security (Auth, injection, XSS)
   - [ ] Performance/Load
   - [ ] Accessibility
   - [ ] Mobile-specific gestures

### 5. Data-Driven Test Coverage
   - [ ] Minimal (2-3 data variations)
   - [ ] Standard (Boundary values + valid/invalid)
   - [ ] Comprehensive (All equivalence partitions)
```

---

## 🏭 Domain-Specific Templates

### E-Commerce Domain

```markdown
### E-Commerce Specific Test Categories

Additional tags to include:
- `@Inventory` - Stock management, reservations
- `@Payment` - Payment gateway integration
- `@Shipping` - Delivery calculations, tracking
- `@Cart` - Add/remove, persistence, abandoned cart
- `@Checkout` - Multi-step flows, guest checkout
- `@Discount` - Coupons, promotions, bulk pricing
- `@Wishlist` - Save for later, sharing
- `@Returns` - Refund flows, RMA

### Critical E-Commerce Scenarios

```gherkin
@E2E.Critical.Checkout.Guest @Payment.Stripe @PCI.Compliance
Scenario: Guest checkout with credit card
  Given the guest user has products in cart
  When they proceed to checkout as guest
  And enter shipping details
  And enter valid credit card information
  And place the order
  Then the order should be confirmed
  And payment should be authorized
  And inventory should be deducted
  And confirmation email should be sent
```

### Data-Driven Payment Tests
```gherkin
@API.Critical.Payment.Processing @DataDriven @Boundary
Scenario Outline: Payment with various card types
  When a payment is processed with card "<card_type>"
  Then the response should be "<expected_result>"
  And the transaction status should be "<status>"
  
  Examples:
    | card_type | expected_result | status |
    | VISA_VALID | success | approved |
    | MASTERCARD_VALID | success | approved |
    | AMEX_VALID | success | approved |
    | VISA_DECLINED | failure | declined |
    | EXPIRED_CARD | failure | expired |
    | INVALID_CVV | failure | invalid_cvv |
    | INSUFFICIENT_FUNDS | failure | insufficient_funds |
```
```

### Healthcare Domain

```markdown
### Healthcare Specific Considerations

Additional tags:
- `@HIPAA` - Privacy compliance
- `@PHI` - Protected Health Information handling
- `@Audit` - Audit trail requirements
- `@Consent` - Patient consent flows
- `@Integration.HL7` - HL7 FHIR integration
- `@Integration.DICOM` - Medical imaging
- `@Emergency` - Break-glass procedures

### HIPAA Compliance Tests
```gherkin
@Security.Critical.HIPAA.PHI_Access @Audit.Required
Scenario: Unauthorized PHI access attempt is logged
  Given a user without PHI access permission
  When the user attempts to view patient "P12345" records
  Then access should be denied
  And the attempt should be logged with timestamp
  And security team should be notified
  And the patient ID should not appear in error messages
```
```

### Financial Domain

```markdown
### Financial/Banking Specific Considerations

Additional tags:
- `@PCI_DSS` - Payment Card Industry compliance
- `@SOX` - Sarbanes-Oxley compliance
- `@KYC` - Know Your Customer
- `@AML` - Anti-Money Laundering
- `@Transaction` - Money movement
- `@Reconciliation` - End-of-day balancing
- `@MultiCurrency` - FX, currency conversion

### Idempotency Tests
```gherkin
@API.Critical.Transaction.Idempotency @Finance @Retry.Safe
Scenario: Duplicate transaction request is idempotent
  Given a transaction with idempotency key "IDEMP-001"
  When the transaction is submitted twice
  Then only one transaction should be recorded
  And both requests should return the same response
  And the account should be debited only once
```
```

---

## 📤 Output Formats

### Format 1: Gherkin Feature Files (Primary)
```gherkin
# features/authentication/login.feature
@Feature.Authentication @Owner.QA_Team @Sprint.23
Feature: User Authentication
  As a registered user
  I want to securely log into the system
  So that I can access my personalized dashboard

  Background:
    Given the authentication service is available
    And the user database is seeded with test accounts

  @Smoke.Critical @TestId.TC-AUTH-001
  Scenario: Successful login with valid credentials
    Given the user navigates to "/login"
    When the user enters username "test.user@example.com"
    And the user enters password "ValidPass123!"
    And the user clicks "Sign In" button
    Then the user should be redirected to "/dashboard"
    And the URL should contain "welcome=true"
    And the user avatar should be visible
```

### Format 2: Test Case Table (For Test Management Tools)

| Test ID | Tags | Feature | Scenario Name | Precondition | Steps | Expected Result | Priority | Automation |
|---------|------|---------|---------------|--------------|-------|-----------------|----------|------------|
| TC-AUTH-001 | @Smoke @Critical @Functional | Authentication | Valid login | User exists | 1. Navigate to login<br>2. Enter credentials<br>3. Click Sign In | Dashboard displayed | P0 | Yes |
| TC-AUTH-002 | @Negative @Validation @Security | Authentication | SQL injection attempt | Login page accessible | 1. Enter SQL payload<br>2. Submit | Error without DB details | P1 | Yes |

### Format 3: JSON (For Automation Frameworks)

```json
{
  "test_plan": {
    "project": "E-Commerce Platform",
    "version": "2.1",
    "features": [
      {
        "name": "Authentication",
        "scenarios": [
          {
            "id": "TC-AUTH-001",
            "tags": ["@Smoke", "@Critical", "@Functional"],
            "name": "Successful login with valid credentials",
            "type": "positive",
            "bdd": {
              "given": ["the user is on the login page"],
              "when": ["the user enters valid credentials", "clicks login"],
              "then": ["the user should be redirected to dashboard"]
            },
            "automation": {
              "framework": "playwright",
              "parallel": true,
              "retry": 0
            }
          }
        ]
      }
    ]
  }
}
```

---

## ✅ Quality Gates

### Pre-Generation Checklist
- [ ] All mandatory context fields provided
- [ ] Domain identified for specialized rules
- [ ] User roles defined
- [ ] Integration points listed
- [ ] Compliance requirements noted

### Post-Generation Checklist
- [ ] Every feature has @Smoke coverage
- [ ] Every positive scenario has negative counterpart
- [ ] All API endpoints have @Contract tests
- [ ] Data-driven tests include boundary values
- [ ] Tags follow naming convention
- [ ] No orphaned steps (all referenced in scenarios)
- [ ] Scenario names are descriptive and unique

### Automation-Readiness Verification
- [ ] All steps are atomic (single action/assertion)
- [ ] Locators are described (if UI tests)
- [ ] API tests include status codes
- [ ] Data variations are clearly specified
- [ ] Test data setup is documented

---

## 🔄 Continuous Improvement

### Feedback Loop
```markdown
After each test execution cycle, capture:
1. Which tests found bugs? (Prioritize similar patterns)
2. Which tests never fail? (Consider reducing frequency)
3. Which scenarios are missing? (Update patterns)
4. What new edge cases were discovered? (Add to library)
```

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2024-03 | Complete rewrite with BDD-first approach, clarification framework, data-driven patterns |
| 1.1 | 2024-01 | Added API testing templates |
| 1.0 | 2023-11 | Initial version |

---

> **💡 Pro Tip:** Always run the `@Smoke` suite first. If smoke tests fail, don't proceed with full regression.
