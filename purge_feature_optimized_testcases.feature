Feature: Purge Feature - Comprehensive Test Suite
  # As an administrator
  # I want to configure and manage purge rules for data retention
  # So that records can be automatically archived or deleted based on business policies

  # ============================================================================
  # GLOBAL SETTINGS SCENARIOS
  # ============================================================================

  # @Functional @GlobalSettings @Positive
  # Scenario: Enable purge feature from application settings
  #   Given the user is logged in as an administrator
  #   And the user navigates to "Agent Portal -> Application Settings"
  #   When the user toggles "Enable purge" setting to "On"
  #   And the user clicks "Save" button
  #   Then the purge feature should be enabled successfully
  #   And the user should be able to create purge rules in Studio

  # @Functional @GlobalSettings @Negative
  # Scenario: Disable purge feature and verify rules are inactive
  #   Given the purge feature is enabled
  #   And there are existing active purge rules configured
  #   When the user toggles "Enable purge" setting to "Off"
  #   And the user clicks "Save" button
  #   Then the purge feature should be disabled
  #   And all existing purge rules should become inactive
  #   And no purge operations should be executed

  # @E2E @GlobalSettings @check
  # Scenario: Verify default state of purge feature on fresh installation
  #   Given a new tenant is provisioned
  #   When the administrator accesses Application Settings
  #   Then the "Enable purge" toggle should be set to "Off" by default
  #   And the purge configuration options should be hidden or disabled

  # ============================================================================
  # RULE CREATION SCENARIOS
  # ============================================================================

  @Functional @RuleManagement @Positive @Critical
  Scenario: Create a new purge rule with all required fields
    Given the user is logged in as an administrator
    And the user navigates to "Agent Portal -> Studio"
    And the user selects an entity
    And the user navigates to Cross-record settings
    When the user clicks "Add" button to create new rule
    And the user enters "Rule name" as "INC_Purge_Rule_01"
    And the user enters "Display name" as "Incident Purge Rule"
    And the user selects record type "Incident"
    And the user enables "Soft deletion"
    And the user selects closed phases "Closed" and "Abandoned"
    And the user configures recurrence by selecting "Every day" or specific days "Monday" and "Tuesday"
    And the user sets "Max execution time" to a value greater than 0
    And the user clicks "Save" button
    Then the purge rule should be created successfully
    And recurrence configuration should be saved successfully
    And "Max execution time" should be accepted only when greater than 0
    And the rule should appear in the rules list

  @Functional @RuleManagement @Positive
  Scenario: Create purge rule with both soft and hard deletion enabled
    Given the user is creating a new purge rule
    When the user enters valid rule name, display name and recurrence fields
    And the user selects record type "Request"
    And the user enables "Soft deletion"
    And the user enables "Hard deletion"
    And the user selects appropriate closed phases
    And the user clicks "Save" button
    Then the purge rule should be created with both deletion types
    And "Soft deletion" column should show "Yes"
    And "Hard deletion" column should show "Yes"

  @Functional @RuleManagement @HardDelete @Acknowledgement
  Scenario: Show hard deletion acknowledgement popup when creating rule with hard deletion entities
    Given the user is creating a new purge rule
    And the user selects entity types "Aviator session" and "Aviator usage"
    And the user enables both "Soft deletion" and "Hard deletion"
    When the user clicks "OK" button to save selected entities
    Then "Hard deletion warning" acknowledgement popup should be displayed
    And the popup should list entities "Aviator session" and "Aviator usage"
    When the user checks acknowledgement checkbox
    And the user clicks "CONFIRM" button
    Then selected entities should be saved in the purge rule

  @Functional @RuleManagement @HardDelete @Acknowledgement @Negative
  Scenario: Do not save hard deletion entity selection when acknowledgement is not accepted
    Given the user is creating or editing a purge rule
    And the user enables both "Soft deletion" and "Hard deletion"
    And the user has selected entities with hard deletion enabled
    When the user clicks "OK" button to save selected entities
    Then "Hard deletion warning" acknowledgement popup should be displayed
    When the user does not check acknowledgement checkbox
    And the user clicks "CONFIRM" button
    Then selected entities should not be saved
    And user should remain on acknowledgement popup or see validation message

  @Functional @RuleManagement @HardDelete @Acknowledgement @Negative
  Scenario: verify acknowledgement should not be accepted until acknowledgement checkbox is selected
    Given the user is creating or editing a purge rule
    And the user has selected entities with hard deletion enabled
    When the user clicks "OK" button to save selected entities
    Then "Hard deletion warning" acknowledgement popup should be displayed
    And acknowledgement checkbox should be unchecked by default
    When the user checks acknowledgement checkbox
    And clicked "CONFIRM" button
    Then acknowledgement should be accepted and entities should be saved in the purge rule
    
  @Functional @RuleManagement @Positive
  Scenario: Create purge rule for custom entity
    Given a custom entity "Custom_Record_01" exists in the system
    When the user navigates to Cross-record settings for custom entity
    And the user creates a purge rule for "Custom_Record_01"
    And the user selects appropriate end phases
    Then the rule should be created successfully
    And the rule should appear in the entity-specific rules list

#untitle rule name 

  # @Functional @RuleManagement @Negative 
  # Scenario: Create purge rule without rule name
  #   Given the user is on the purge rule creation page
  #   When the user leaves "Rule name" field empty
  #   And the user selects record type "Incident"
  #   And the user enables soft deletion
  #   And the user clicks "Save" button
  #   Then the system should display validation error for rule name
  #   And the rule should not be created

  @Functional @RuleManagement @Negative
  Scenario: Create purge rule without selecting any record type
    Given the user is on the purge rule creation page
    When the user enters valid rule name "Test_Rule" and selected all required fields except record type
    And the user does not select any record type
    And the user enables soft deletion
    And the user clicks "Save" button
    Then the system should display validation error for record type
    And the rule should not be created

  @Functional @RuleManagement @Negative
  Scenario: Attempt to enable hard deletion without enabling soft deletion
    Given the user is on the purge rule creation page
    When the user enters valid rule name, display name and recurrence fields
    And the user selects record type "Change"
    And the user does NOT enable "Soft deletion"
    And the user tries to enable "Hard deletion"
    Then the "Hard deletion" checkbox should be disabled
    And a tooltip should display dependency message
#3dot

  # @Functional @RuleManagement @Boundary @check
  # Scenario Outline: Create purge rule with various name lengths
  #   Given the user is on the purge rule creation page
  #   When the user enters rule name with <RuleNameLength> characters
  #   And the user enters display name with <DisplayNameLength> characters
  #   And the user configures all other required fields
  #   And the user clicks "Save" button
  #   Then the system should <ExpectedResult>

  #   Examples:
  #     | RuleNameLength | DisplayNameLength | ExpectedResult                           |
  #     | 50             | 50                | create the rule successfully             |
  #     | 100            | 100               | create the rule successfully             |
  #     | 101            | 100               | display validation error for rule name length |

  @Functional @RuleManagement @SpecialCharacters
  Scenario Outline: Create purge rule with special characters in name fields
    Given the user is on the purge rule creation page
    When the user enters rule name as "<RuleName>"
    And the user configures all other required fields
    And the user clicks "Save" button
    Then the system should <ExpectedResult>

    Examples:
      | RuleName            | ExpectedResult             |
      | Rule_123-Test       | accept and create the rule |
      | Rule@#$%            | accept and create the rule |
      | Rule<script>        | accept and create the rule |
      | Rule With Spaces    | accept and create the rule |

  @Exploratory @RuleManagement @check
  Scenario: Create multiple purge rules for same entity with different phases
    Given the user has created a purge rule for "Incident" with phase "Closed"
    When the user creates another rule for "Incident" entity
    And the user tries to select phase "Closed"
    Then phase "Closed" should be disabled or hidden
    And the user should only see available phases like "Abandoned"
    And the second rule should be created successfully with different phases

  @Functional @RuleManagement @Duplicate
  Scenario: Attempt to create duplicate purge rule with same name
    Given a purge rule named "INC_Rule_01" already exists
    When the user tries to create another rule with name "INC_Rule_01"
    And the user configures all required fields
    And the user clicks "Save" button
    Then the system should display error "Rule name already exists"
    And the duplicate rule should not be created

  # ============================================================================
  # RULE MODIFICATION SCENARIOS
  # ============================================================================

  @Functional @RuleManagement @Positive
  Scenario: Modify existing purge rule display name
    Given an existing purge rule "INC_Rule_01" exists
    When the user selects the rule for editing
    And the user changes "Display name" to "Updated Display Name"
    And the user clicks "Save" button
    Then the rule should be updated successfully
    And the updated display name should be reflected in the list

  @Functional @RuleManagement @Positive
  Scenario: Add hard deletion to existing soft-only purge rule
    Given a purge rule exists with only soft deletion enabled
    When the user edits the rule
    And the user enables "Hard deletion" checkbox
    And the user configures hard delete duration
    And the user clicks "Save" button
    Then the rule should be updated with hard deletion enabled
    And both soft and hard deletion should be active for the rule

  @Functional @RuleManagement @HardDelete @Acknowledgement
  Scenario: Show hard deletion acknowledgement popup only when entity selection changes during edit
    Given an existing purge rule has hard deletion enabled for entity "Aviator session"
    When the user edits the rule and adds entity "Aviator usage"
    And the user clicks "OK" button to save selected entities
    Then "Hard deletion warning" acknowledgement popup should be displayed
    And the popup should list newly changed hard deletion entities

  @Functional @RuleManagement @HardDelete @Acknowledgement
  Scenario: Do not show hard deletion acknowledgement popup when entity selection is unchanged
    Given an existing purge rule has hard deletion enabled for entities "Aviator session" and "Aviator usage"
    When the user opens edit mode and keeps the same entity selection
    And the user clicks "OK" button to save selected entities
    Then "Hard deletion warning" acknowledgement popup should not be displayed
    And the purge rule should be saved successfully

  @Functional @RuleManagement @Negative
  Scenario: Modify rule to remove all closed phases selection
    Given an existing purge rule with phases "Closed" and "Abandoned" selected
    When the user edits the rule
    And the user deselects all closed phases
    And the user clicks "Save" button
    Then the system should save the rule successfully as "Abandoned" phase is still selected

  @Functional @RuleManagement @Conflict
  Scenario: Modify rule to use phase already used in another rule
    Given Rule A uses phase "Closed" for Incident entity
    And Rule B uses phase "Abandoned" for Incident entity
    When the user edits Rule B
    And the user tries to add phase "Closed"
    Then phase "Closed" should be disabled with indicator
    And user should not be able to select already used phase

  @Functional @RuleManagement @Discard
  Scenario: Discard changes made to purge rule
    Given the user is editing an existing purge rule
    And the user has made several changes to the configuration
    When the user clicks "Discard" button
    Then a confirmation dialog should appear
    And upon confirmation all changes should be discarded
    And the original rule configuration should be retained

  # ============================================================================
  # RULE DELETION SCENARIOS
  # ============================================================================

  @Functional @RuleManagement @Positive
  Scenario: Delete an existing purge rule
    Given an existing purge rule "INC_Rule_01" exists
    When the user selects the rule from the list
    And the user clicks "Remove" button
    Then a confirmation dialog should appear
    And upon confirmation the rule should be deleted
    And the rule should no longer appear in the list

  @Functional @RuleManagement @CancelDelete
  Scenario: Cancel purge rule deletion
    Given an existing purge rule is selected
    When the user clicks "Remove" button
    And the confirmation dialog appears
    And the user clicks "Cancel" on the dialog
    Then the rule should not be deleted
    And the rule should remain in the list

  @E2E @RuleManagement
  Scenario: Verify phase availability after rule deletion
    Given Rule A uses phase "Closed" for Incident entity
    When the user deletes Rule A
    And the user creates a new rule for Incident entity
    Then phase "Closed" should now be available for selection
    And the user should be able to create rule with "Closed" phase

  # ============================================================================
  # DURATION VALIDATION SCENARIOS
  # ============================================================================

  @Functional @Validation @Boundary @Critical
  Scenario: Verify minimum gap between soft and hard delete days validation fails
    Given the user is configuring purge durations
    When the user sets soft delete duration to 0 years 0 months 2 days
    And the user sets hard delete duration to 0 years 0 months 1 day
    And the gap between soft and hard delete is less than 3 days
    And the user clicks "Save" button
    Then the system should display validation error
    And the message should indicate hard delete days must be at least 3 days greater than soft delete days

  # @Functional @Validation @Boundary
  # Scenario: Verify combined duration validation 4 days passes
  #   Given the user is configuring purge durations
  #   When the user sets soft delete duration to 0 years 0 months 3 days
  #   And the user sets hard delete duration to 0 years 0 months 1 day
  #   And the combined duration equals 4 days
  #   And the user clicks "Save" button
  #   Then the configuration should be saved successfully
  #   And validation should pass for duration greater than 3 days

  @Functional @Validation @Boundary
  Scenario Outline: Verify various duration combinations validation
    Given the user is configuring purge durations
    When the user sets soft delete to <SoftY> years <SoftM> months <SoftD> days
    And the user sets hard delete to <HardY> years <HardM> months <HardD> days
    Then the validation should <Result> based on gap between soft and hard delete days

    Examples:
      | SoftY | SoftM | SoftD | HardY | HardM | HardD | Result |
      | 0     | 0     | 2     | 0     | 0     | 1     | Fail   |
      | 0     | 0     | 1     | 0     | 0     | 4     | Pass   |
      | 0     | 0     | 5     | 0     | 0     | 2     | Fail   |
      | 0     | 1     | 0     | 0     | 0     | 5     | Pass   |
      | 1     | 0     | 0     | 0     | 0     | 10    | Pass   |
      | 0     | 0     | 0     | 0     | 0     | 3     | Pass   |
      | 0     | 0     | 0     | 0     | 0     | 4     | Pass   |
      | 0     | 0     | 1     | 0     | 0     | 3     | Fail   |
      | 0     | 0     | 5     | 0     | 0     | 8     | Pass   |

  @Functional @Validation @Negative
  Scenario: Attempt to enter negative values for duration fields
    Given the user is configuring purge durations
    When the user tries to enter negative value in year field
    And the user tries to enter negative value in month field
    And the user tries to enter negative value in day field
    Then the field should not accept negative values
    And the system should display validation error

  @Functional @Validation @Boundary
  Scenario Outline: Verify maximum allowed duration values
    Given the user is configuring purge durations
    When the user enters <Years> years <Months> months <Days> days
    And the user clicks "Save" button
    Then the system should <ExpectedResult>

    Examples:
      | Years | Months | Days | ExpectedResult                          |
      | 100   | 0      | 0    | accept based on system limits |
      | 10    | 120    | 0    | accept based on system limits |
      | 0     | 0      | 9999 | accept based on system limits |

  @Functional @Validation
  Scenario: Verify soft delete with 1 day and hard delete enabled
    Given hard deletion is enabled for a rule
    When the user sets soft delete duration to 0 years 0 months 1 days
    And the user sets hard delete duration to 0 years 0 months 4 days
    Then the system should accept this configuration
    And validation should pass as hard delete days is at least 3 days greater than soft delete days

  @Functional @Validation @Negative @Critical
  Scenario: Verify save fails when soft delete is 0 and hard delete is less than 3 days
    Given the user is configuring a purge rule
    When the user sets soft delete duration to 0 years 0 months 0 days
    And the user sets hard delete duration to 0 years 0 months 2 days
    And the user enables both soft and hard deletion
    And the user selects appropriate closed phases
    And the user clicks "Save" button
    Then the system should display validation error
    And the message should indicate hard delete duration must be greater than or equal to 3 days when soft delete is 0 days
    And the rule should not be saved

  @Functional @Validation
  Scenario: Verify soft delete can be zero when hard delete is greater than or equal to 3 days
    Given the user is configuring a purge rule
    When the user sets soft delete duration to 0 years 0 months 0 days
    And the user sets hard delete duration to 0 years 0 months 3 days
    And the user enables both soft and hard deletion
    And the user selects appropriate closed phases
    And the user clicks "Save" button
    Then the system should accept this configuration
    And validation should pass as hard delete days is greater than or equal to 3 days

  @Functional @Validation @Boundary
  Scenario Outline: Verify soft delete 0 days validation based on hard delete days
    Given the user is configuring a purge rule
    When the user sets soft delete duration to <Years> years <Months> months <Days> days
    And the user sets hard delete duration to 0 years 0 months <HardDays> days
    And the user enables soft deletion
    And the user enables hard deletion
    And the user selects appropriate closed phases
    And the user clicks "Save" button
    Then the system should <ExpectedResult>

    Examples:
      | Years | Months | Days | HardDays | ExpectedResult                                                                                |
      | 0     | 0      | 0    | 2        | display validation error because hard delete must be greater than or equal to 3 days when soft delete is 0 |
      | 0     | 0      | 0    | 3        | accept the configuration and save the rule                                                    |
      | 0     | 0      | 0    | 5        | accept the configuration and save the rule                                                    |

  # ============================================================================
  # SCHEDULE CONFIGURATION SCENARIOS
  # ============================================================================

  @Functional @Schedule @Positive
  Scenario: Configure daily purge schedule
    Given the user is configuring a purge rule schedule
    When the user sets soft delete duration to 1 year
    And the user sets hard delete duration to 1 year and 4 days
    And the user sets schedule start time to "12:00"
    And the user sets max execution time to 2 hours
    And the user enables "Every day" recurrence
    And the user clicks "Save" button
    Then the schedule should be saved successfully
    And purge should run daily at the configured time

  @Functional @Schedule @Positive
  Scenario: Configure weekly purge schedule for specific days
    Given the user is configuring a purge rule schedule
    When the user sets soft delete duration to 30 days
    And the user sets hard delete duration to 34 days
    And the user disables "Every day" recurrence
    And the user selects days Monday Wednesday Friday
    And the user clicks "Save" button
    Then the schedule should be saved successfully
    And purge should run only on selected days

  @Functional @Schedule @Positive
  Scenario: Configure weekend only purge schedule
    Given the user is configuring a purge rule schedule
    When the user sets soft delete duration to 10 days
    And the user sets hard delete duration to 14 days
    And the user disables "Every day" recurrence
    And the user selects days Saturday and Sunday only
    And the user clicks "Save" button
    Then the schedule should be saved successfully
    And purge should run only on weekends

  @Functional @Schedule @Negative
  Scenario: Configure schedule without selecting any day
    Given the user is configuring a purge rule schedule
    When the user sets soft delete duration to 5 days
    And the user sets hard delete duration to 9 days
    And the user disables "Every day" recurrence
    And the user does not select any day of the week
    And the user clicks "Save" button
    Then the system should display validation error
    And the message should indicate at least one day must be selected

  # @Functional @Schedule @Boundary
  # Scenario Outline: Verify schedule start time format validation
  #   Given the user is configuring purge schedule
  #   When the user enters schedule start time as "<TimeValue>"
  #   Then the system should <Result> the time format

  #   Examples:
  #     | TimeValue | Result |
  #     | 12:00     | Accept |
  #     | 23:59     | Accept |
  #     | 00:00     | Accept |
  #     | 24:00     | Reject |
  #     | 12:60     | Reject |
  #     | abc       | Reject |
  #     |           | Reject |

  @Functional @Schedule @Multiple
  Scenario: Create multiple schedules for different purge rules
    Given purge Rule A exists with schedule "Daily Purge"
    When the user creates purge Rule B
    And the user configures schedule "Weekly Purge" for Rule B
    And the user configures different timing and days
    Then both schedules should be saved independently
    And each rule should execute based on its own schedule

  @Functional @Schedule @MaxExecution
  Scenario Outline: Configure max execution time boundaries
    Given the user is configuring purge schedule
    When the user sets max execution time to "<Hours>" hours
    Then the system should <Result>

    Examples:
      | Hours | Result                     |
      | 1     | Accept the value           |
      | 2     | Accept the value           |
      | 24    | Accept the value           |
      | 0     | Accept the value           |
      | -1    | Reject the value           |
      | 25    | reject based on maximum limit |

  # ============================================================================
  # RULE ACTIVATION/DEACTIVATION SCENARIOS
  # ============================================================================

  @Functional @Activation @Positive
  Scenario: Activate a purge rule using On/Off toggle
    Given a purge rule exists in "Off" state
    When the user toggles the rule to "On"
    And the user clicks "Save" button
    Then the rule should be activated
    And purge operations should be scheduled as per configuration

  @Functional @Activation @Positive
  Scenario: Deactivate an active purge rule
    Given a purge rule exists in "On" state
    When the user toggles the rule to "Off"
    And the user clicks "Save" button
    Then the rule should be deactivated
    And no further purge operations should be scheduled for this rule
    And any pending purge jobs should be cancelled

  @E2E @Activation
  Scenario: Verify deactivated rule does not purge records
    Given a purge rule is configured and active
    And records exist that meet purge criteria
    When the user deactivates the rule before scheduled execution
    And the scheduled time passes
    Then the records should NOT be purged
    And records should remain in their current state

  @Functional @Activation @Bulk
  Scenario: Activate multiple rules simultaneously
    Given multiple purge rules exist in "Off" state
    When the user activates Rule A
    And the user activates Rule B
    And the user activates Rule C
    And the user clicks "Save" button
    Then all activated rules should be scheduled
    And each rule should execute independently

  # ============================================================================
  # RECORD TYPE SELECTION SCENARIOS
  # ============================================================================

  @Functional @RecordType @OOTB
  Scenario: Select OOTB entity types for purge
    Given the user is creating a purge rule
    When the user selects entity type "Incident"
    And the user also selects entity type "Change"
    And the user configures other required fields
    Then the rule should be created for selected OOTB entities
    And the entity types should be displayed in the rule details

  @Functional @RecordType @Custom
  Scenario: Select custom entity types for purge
    Given custom entities exist in the system
    When the user is creating a purge rule
    And the user selects custom entity "Custom_01"
    And the user configures other required fields
    Then the rule should be created for the custom entity
    And custom entity should appear in the record types list

  @Functional @RecordType @Mixed
  Scenario: Select combination of OOTB and custom entity types
    Given both OOTB and custom entities exist
    When the user is creating a purge rule
    And the user selects "Request" OOTB
    And the user selects "Custom_Record_Name" Custom
    And the user configures other required fields
    Then the rule should be created for both entity types
    And both should be displayed in the rule configuration

  @Functional @RecordType @All
  Scenario: Select all available record types
    Given multiple entity types exist in the system
    When the user is creating a purge rule
    And the user selects all available record type checkboxes
    And the user configures other required fields
    Then the rule should be created for all selected entities
    And the rule should apply to all selected record types

  # ============================================================================
  # END PHASE SELECTION SCENARIOS
  # ============================================================================

  @Functional @Phase @Positive
  Scenario: Select single end phase for purge rule
    Given the user is configuring a purge rule
    When the user selects entity type "Incident"
    And the user views available end phases
    And the user selects phase "Closed" only
    And the user completes rule configuration
    Then the rule should purge only records in "Closed" phase

  @Functional @Phase @Positive
  Scenario: Select multiple end phases for purge rule
    Given the user is configuring a purge rule
    When the user selects entity type "Incident"
    And the user selects phases "Closed" and "Abandoned"
    And the user completes rule configuration
    Then the rule should purge records in either "Closed" or "Abandoned" phase

  @Functional @Phase @Conflict
  Scenario: Verify disabled phases already used in other rules
    Given Rule A exists for Incident with phase "Closed" selected
    When the user creates a new Rule B for Incident
    And the user views available end phases
    Then phase "Closed" should be disabled or grayed out
    And the user should not be able to select "Closed" phase
    And other unused phases should remain enabled

  @Functional @Phase @Custom
  Scenario: Select end phases for custom entity
    Given a custom entity with custom workflow exists
    And the custom workflow has end phases "End point 01" and "End point 02"
    When the user creates a purge rule for the custom entity
    Then the custom end phases should be displayed
    And the user should be able to select custom end phases

  @Functional @Phase @All
  Scenario: Select all available end phases for an entity
    Given an entity has end phases Closed Abandoned Phase 03
    When the user creates a purge rule
    And the user selects all available end phases
    Then all phases should be marked for purging
    And the rule should apply to records in any end phase

  # ============================================================================
  # AUDIT TRAIL SCENARIOS
  # ============================================================================

  @Functional @Audit @Positive
  Scenario: Verify audit log entry for purge rule creation
    Given the user has created a new purge rule
    When the user navigates to Agent Portal -> Administration -> Audit
    Then an audit entry should exist for the rule creation
    And the entry should contain rule name timestamp and user details
    And the action type should be "CREATE"

  @Functional @Audit @Positive
  Scenario: Verify audit log entry for purge rule modification
    Given the user has modified an existing purge rule
    When the user navigates to Audit section
    Then an audit entry should exist for the rule modification
    And the entry should contain before and after values
    And the action type should be "UPDATE"

  @Functional @Audit @Positive
  Scenario: Verify audit log entry for purge rule deletion
    Given the user has deleted a purge rule
    When the user navigates to Audit section
    Then an audit entry should exist for the rule deletion
    And the entry should contain deleted rule details
    And the action type should be "DELETE"

  @Functional @Audit @Positive
  Scenario: Verify audit log for purge execution
    Given a purge rule is active and scheduled
    When the purge job executes at scheduled time
    And records are purged soft or hard
    Then audit entries should be created for purge execution
    And entries should contain number of records processed
    And execution start time end time and status

  @E2E @Audit
  Scenario: Verify audit trail completeness for compliance
    Given multiple purge operations have been performed
    When the user reviews the audit history
    Then all purge-related actions should be logged
    And the audit trail should be immutable
    And entries should not be deletable by administrators

  # ============================================================================
  # SOFT DELETE RECORDS RECOVERY SCENARIOS
  # ============================================================================

  @E2E @Recovery @SoftDelete
  Scenario: Verify soft deleted records are not directly visible
    Given records have been soft deleted by purge operation
    When a regular user searches for the deleted records
    And the user checks standard list views and search results
    Then the soft deleted records should not appear
    And the records should be excluded

  # @E2E @Recovery @Support
  # Scenario: Verify support team can retrieve soft deleted records
  #   Given records have been soft deleted by purge operation
  #   When the support team receives a recovery request
  #   And the support team uses appropriate tools or queries
  #   Then the support team should be able to view soft deleted records
  #   And the support team should be able to restore the records if needed

  # @Functional @SoftDelete @DataIntegrity
  # Scenario: Verify soft deleted records retain all data and relationships
  #   Given a record with related data attachments history related records
  #   When the record is soft deleted by purge operation
  #   Then all record data should be preserved
  #   And relationships should be maintained
  #   And the record should be recoverable with all data intact

  # ============================================================================
  # HARD DELETE RECORDS SCENARIOS
  # ============================================================================

  @E2E @HardDelete @Permanent
  Scenario: Verify hard deleted records are permanently removed
    Given records have been soft deleted by purge operation
    And the hard delete duration has passed
    When the hard purge job executes
    Then the records should be permanently deleted from the database
    # And the records should not be recoverable
    # And storage space should be freed

  # @E2E @HardDelete @DataCleanup
  # Scenario: Verify hard delete removes all related data
  #   Given a record with attachments history and related records exists
  #   And the record has been soft deleted
  #   When the hard purge job executes for this record
  #   Then the main record should be deleted
  #   And all related data should be cleaned up


  # @Functional @HardDelete @Cascade
  # Scenario: Verify cascade delete behavior for related records
  #   Given a parent record with child records exists
  #   And purge rules are configured for both parent and child entities
  #   When the parent record meets hard delete criteria
  #   Then the system should handle child records appropriately
  #   Based on configured cascade delete rules

  # ============================================================================
  # UI/UX SCENARIOS
  # ============================================================================

  @UI @Navigation
  Scenario: Verify navigation flow to purge configuration
    Given the user is logged into Agent Portal
    When the user navigates to Studio
    And the user selects an entity
    And the user clicks on Cross-record settings
    And user is clicking "purge configuration" tab
    Then the purge rule configuration page should load
    And all UI elements should be displayed correctly

  @UI @Layout
  Scenario: Verify purge rule configuration page layout
    Given the user is on purge rule configuration page
    Then the page should display Add and Remove buttons
    And Save and Discard buttons should be present
    And On/Off toggle should be visible
    And the rules list should be displayed on the left
    And the configuration form should be on the right

  @UI @Modal
  Scenario: Verify record type selection modal
    Given the user clicks "Configure records" button
    Then a modal dialog should open
    And the modal should display available record types list
    And checkboxes should be available for selection
    And Enable Soft Delete and Enable Hard Delete options should be present
    And Lifecycle end phase section should be displayed
    And the modal should have Save and Cancel buttons

  # @UI @GlobalSettings
  # Scenario: Verify Enable purge toggle UI elements
  #   Given the user is on Application Settings page
  #   When the user views the "Enable purge" section
  #   Then the section should display descriptive text about purge feature
  #   And the toggle should have "On" and "Off" states
  #   And Save and Discard buttons should be available

  @UI @RecordType
  Scenario: Verify record type selection UI elements
    Given the user is on the record type selection modal
    When the user views the available options
    Then checkboxes should be displayed for each entity type
    And a search field should be available
    And selected count should be displayed
    And Deletion type and Lifecycle end phase sections should update based on selection

  @UI @Responsive
  Scenario Outline: Verify UI responsiveness on different screen sizes
    Given the user accesses purge configuration on different devices
    When the screen resolution is <Resolution>
    Then all UI elements should be accessible and properly aligned
    And no elements should overlap or be cut off

    Examples:
      | Resolution | ExpectedBehavior                      |
      | 1920x1080  | Full layout with side-by-side panels  |
      | 1366x768   | Adjusted layout all elements visible  |
      | 1024x768   | Responsive layout scrolling if needed |
      | 768x1024   | Tablet-friendly layout                |
      | 375x667    | Mobile-friendly layout                |

  @UI @Accessibility
  Scenario: Verify keyboard navigation for purge configuration
    Given the user is on purge configuration page
    When the user navigates using Tab key
    Then all interactive elements should be focusable
    And Enter or Space should activate buttons and toggles
    And form fields should be accessible via keyboard

  # ============================================================================
  # PERMISSIONS AND SECURITY SCENARIOS
  # ============================================================================

  @Security @Permissions @Positive
  Scenario: Verify administrator can access purge configuration
    Given a user with Administrator role logs in
    When the user attempts to access purge configuration
    Then the user should be able to access all purge settings
    And the user should be able to create modify and delete rules

  # @Security @Permissions @Negative
  # Scenario Outline: Verify non-admin user cannot access purge configuration
  #   Given a user with <Role> role logs in
  #   When the user attempts to access purge configuration
  #   Then the user should receive access denied error
  #   Or the purge configuration menu should not be visible

  #   Examples:
  #     | Role                                 | ExpectedAccess |
  #     | Agent                                | Denied         |
  #     | Viewer                               | Denied         |
  #     | Custom Role without Purge Permission | Denied         |

  # @Security @Audit
  # Scenario: Verify unauthorized access attempts are logged
  #   Given a user without purge permissions
  #   When the user attempts to access purge configuration via direct URL
  #   Then the access attempt should be blocked
  #   And the attempt should be logged in security audit
  #   And appropriate error message should be displayed

  # @Security @Data
  # Scenario: Verify purge rules data is protected from tampering
  #   Given a user attempts to modify purge rules via API
  #   When the request is sent without proper authentication
  #   Or the request is sent with insufficient permissions
  #   Then the request should be rejected
  #   And no changes should be made to purge rules

  # ============================================================================
  # E2E INTEGRATION SCENARIOS
  # ============================================================================

  @E2E @Integration @FullFlow
  Scenario: End-to-end purge workflow for Incident entity
    Given a purge rule is created for Incident entity
    And the rule has soft delete 1 day hard delete 4 days
    And the rule targets "Closed" phase
    And Incidents exist in "Closed" phase older than 1 day
    When the purge job runs as per schedule
    Then eligible Incidents should be soft deleted
    And after 4 days they should be hard deleted
    And audit entries should be created for both operations

  @E2E @Integration @MultipleEntities
  Scenario: End-to-end purge for multiple entity types simultaneously
    Given purge rules exist for Incident Request and Change
    And each rule has different duration configurations
    When the scheduled purge job runs
    Then records from all configured entities should be processed
    And each entity should follow its own purge duration rules
    And no interference should occur between entity purges

  @E2E @Integration @JobExecution @check
  Scenario: Verify purge job execution within max execution time
    Given a purge rule is configured with max execution time of 2 hours
    And a large volume of records meets purge criteria
    When the purge job starts execution
    Then the job should complete within 2 hours
    And partial results should be handled appropriately

  @E2E @Integration @Scheduling
  Scenario Outline: Verify purge job scheduling with system timezone
    Given the system timezone is set to <Timezone>
    And a purge rule is scheduled for 12:00
    When the scheduled time arrives in system timezone
    Then the purge job should execute at the correct time
    And the execution should align with configured schedule

    Examples:
      | Timezone | ExpectedExecution |
      | UTC      | 12:00 UTC         |
      | EST      | 12:00 EST         |
      | IST      | 12:00 IST         |
      | PST      | 12:00 PST         |

  # ============================================================================
  # PERFORMANCE SCENARIOS
  # ============================================================================

  # @Performance @Load
  # Scenario Outline: Verify purge performance with large data volume
  #   Given the system has <RecordCount> records eligible for purge
  #   When the purge job executes
  #   Then the purge should complete within acceptable time
  #   And system performance should not degrade significantly

  #   Examples:
  #     | RecordCount | MaxAcceptableTime |
  #     | 10000       | 30 minutes        |
  #     | 100000      | 2 hours           |
  #     | 1000000     | 6 hours           |

  # @Performance @Concurrent
  # Scenario: Verify system behavior during purge execution
  #   Given the purge job is running
  #   When regular users are accessing the system
  #   And performing create read update operations
  #   Then normal operations should not be blocked
  #   And system responsiveness should remain acceptable

  # ============================================================================
  # EDGE CASES AND EXPLORATORY SCENARIOS
  # ============================================================================

  @Exploratory @EdgeCase
  Scenario: Purge rule with special characters in entity names
    Given custom entities exist with special characters in names
    When the user attempts to create purge rules for such entities
    Then the system should handle the names appropriately
    And no errors should occur during rule creation or execution

  @Exploratory @EdgeCase
  Scenario: Rapid toggle of purge enable or disable
    Given the user has access to Enable purge toggle
    When the user rapidly toggles the setting On and Off multiple times
    Then the system should handle the toggles gracefully
    And no corruption should occur in purge rules
    And the final state should be consistent

  @Exploratory @EdgeCase
  Scenario: Concurrent rule modifications by multiple administrators
    Given two administrators are logged in simultaneously
    When Admin A modifies a purge rule
    And Admin B modifies the same rule at the same time
    Then the system should handle concurrency appropriately
    And either optimistic locking or last-write-wins should apply

  # @Exploratory @EdgeCase
  # Scenario: System behavior during purge job failure
  #   Given a purge job is running
  #   When a system error occurs like database connection lost
  #   Then the purge job should fail gracefully
  #   And partial changes should be rolled back or handled
  #   And error should be logged for investigation

  # @Exploratory @EdgeCase
  # Scenario: Purge with records in transition between phases
  #   Given records are transitioning between workflow phases
  #   When the purge job runs during the transition
  #   Then records should be evaluated based on their current state
  #   And no records should be purged incorrectly
  #   And race conditions should be handled properly

  # ============================================================================
  # DATA MIGRATION AND UPGRADE SCENARIOS
  # ============================================================================

  @Migration @Upgrade
  Scenario: Verify purge rules after system upgrade
    Given purge rules exist in the previous version
    When the system is upgraded to new version
    Then all existing purge rules should be preserved
    And rules should remain functional after upgrade
    And no manual reconfiguration should be required

  @Migration @Upgrade @RuleManagement
  Scenario: Verify default purge rule behavior for existing user upgrade from 26.1 to 26.2
    Given an existing user upgrades the system from version "26.1" to "26.2"
    When the user navigates to purge rule configuration
    Then a default purge rule with name "Default" should be available
    And user should be allowed to edit only "Display name" and recurrence fields and can change schedule 
    And user should not be allowed to configure or edit entity selection
    And the following 5 OOTB entities should be selected by default:
      | Entity   |
      | Request  |
      | Incident |
      | Problem  |
      | Change   |
      | Release  |

  # @Migration @Backup
  # Scenario: Verify purge configuration backup and restore
  #   Given purge rules are configured and active
  #   When the system backup is performed
  #   And the system is restored from backup
  #   Then all purge rules should be restored
  #   And rule states On or Off should be preserved
