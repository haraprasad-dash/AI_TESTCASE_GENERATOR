# Enhanced Prompt (Extended from Original)

## Original Prompt:
"Review the user guide at https://staging.docs.microfocus.com/doc/423/26.2/purgeconfiguration using purge_feature_optimized_testcases.feature. Verify that each test case is fully covered, identify coverage gaps, perform accuracy/clarity/consistency checks, ensure traceability between test cases and guide sections, log all defects, and prioritize review actions by severity."

---

## ENHANCED VERSION (Use This):

```
Review the user guide at https://staging.docs.microfocus.com/doc/423/26.2/purgeconfiguration using purge_feature_optimized_testcases.feature. 

## READING INSTRUCTIONS:
1. Fetch and read ALL content from the provided URL:
   - Wait for any dynamic/SPA content to load
   - Extract main documentation text (ignore navigation, headers, footers)
   - If custom instructions specify sections, read only those; otherwise read all

2. Read the ENTIRE purge_feature_optimized_testcases.feature file:
   - Parse all scenario definitions
   - Extract tags, scenario titles, and steps

## TEST CASE FILTERING (CRITICAL):
Before analyzing, FILTER test cases:

EXCLUDE these from analysis:
- Tests tagged with: @Negative, @Exploratory, @EdgeCase, @Performance
- Scenarios with keywords: "attempt to", "verify error", "validation error", "invalid input", "fail", "boundary", "rapid", "concurrent", "stress", "load"
- UI responsiveness tests (screen sizes)
- Accessibility tests (keyboard navigation)

INCLUDE only these in analysis:
- Tests tagged with: @Functional, @E2E, @Integration
- Positive workflow scenarios
- Feature capability descriptions  
- Business rule documentation needs
- Permission and compliance features

## ANALYSIS INSTRUCTIONS:
For each INCLUDED test case, verify against user guide:

1. **Coverage Check**: Is the feature documented?
   - Fully documented = Feature explained with clear steps
   - Partially documented = Mentioned but unclear/incomplete
   - Not documented = Feature exists in product but not in guide

2. **Accuracy Check**: Does documentation match behavior?
   - Steps are correct
   - Configuration options are accurate
   - Business rules are properly explained

3. **Clarity Check**: Is documentation clear to customers?
   - Language is unambiguous
   - Examples are provided where needed
   - Navigation paths are clear

## OUTPUT STRUCTURE:

### 1. FEATURES PROPERLY DOCUMENTED
For each documented feature found:
```
Feature: [Feature Name]
Where to find: [Exact navigation path from user guide]
What it does: [Clear description of functionality]
Customer Benefit: [Why this matters to users]
```

### 2. FEATURES NOT DOCUMENTED (Coverage Gaps)
For each feature from test cases NOT in user guide:
```
Feature: [Feature Name]
What this feature does: [Description from test case]
Why customers need to know: [Business/compliance impact]
Documentation to Add: [Specific suggested text to add to user guide]
```

### 3. DOCUMENTATION NEEDS CLARITY (Consistency Issues)
For each feature that is documented but unclear:
```
Feature: [Feature Name]
Current Documentation: "[Exact quote from user guide]"
Issue: [What's unclear, ambiguous, or misleading]
Corrected Text: [Improved version with clear explanation]
```

## DEFECT LOG:
Log defects with severity:
- **HIGH**: Critical feature missing, incorrect information, compliance gap
- **MEDIUM**: Feature unclear, missing examples, partial documentation
- **LOW**: Minor clarity issues, formatting suggestions

## PRIORITY ACTIONS:
Prioritize review actions by:
1. HIGH severity items first
2. Compliance/security features first
3. Core functionality features next
4. Nice-to-have features last

## CONSTRAINTS:
- Focus ONLY on customer-facing features (exclude negative/edge/exploratory tests)
- Provide specific suggested text for missing documentation
- Format with proper spacing and structure
- Ensure output is readable (avoid text overlap)
```

---

## Key Enhancements Made:

| Aspect | Original | Enhanced |
|--------|----------|----------|
| Reading | Not specified | Explicit URL and file reading instructions |
| Filtering | Not specified | Specific include/exclude tags and keywords |
| Focus | All test cases | Only customer-facing features |
| Output | Not specified | 3-section structured format |
| Defects | Log and prioritize | Severity-based with specific criteria |
| Clarity | Not specified | "Corrected Text" for improvements |
```

This keeps your original intent while adding the necessary details to get the expected output quality. Use the ENHANCED version for testing.