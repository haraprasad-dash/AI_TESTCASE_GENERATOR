Feature: Agent Interface Header Text Color Configuration
  # As a theme user
  # I want to configure the agent interface header text color
  # So that the header text matches my organization's branding

  Background:
    Given the user is logged into the system
    And the user navigates to "Megamenu" > "Theme Settings"
    And the user is in preview mode

# ==========================================
# HAPPY PATH SCENARIOS
# ==========================================

  Scenario: Verify default value is displayed correctly
    When the user views the "Agent interface header text color" field
    Then the field should display the default hex value "#FFFFFF"
    And the agent interface header text should appear in white color

  Scenario: Apply custom hex color to header text
    Given the user clears the "Agent interface header text color" field
    And the user enters "#FF5733" in the field
    When the user clicks the "Save" button
    Then the settings should be saved successfully
    And the agent interface header text should display in orange-red color (#FF5733)
    And the change should be visible to all agent interface users

  Scenario: Apply white text color explicitly
    Given the "Agent interface header text color" field contains "#FFFFFF"
    When the user changes the value to "#000000"
    And clicks "Save & Exit"
    Then the agent interface header text should display in black color
    And the user should be redirected to the previous screen

  Scenario: Apply dark text color for light backgrounds
    Given the "Agent interface header background" is set to a light color (#FFFFFF)
    When the user sets "Agent interface header text color" to "#000000"
    And saves the settings
    Then the agent interface header text should display in black color

  Scenario: Color change visible in new themes
    Given the user creates a new theme named "New Corporate Theme"
    When the user navigates to Theme Settings
    Then the "Agent interface header text color" field should be visible
    And the field should display the default value "#FFFFFF"

  Scenario: Color change visible in existing themes
    Given an existing theme "Legacy Theme" was created before version 26.2
    When the user opens "Legacy Theme" settings
    Then the "Agent interface header text color" field should be visible
    And the field should display the default value "#FFFFFF"


  Scenario: Select color using color picker
    Given the color picker feature is developed and enabled
    When the user clicks the color picker icon next to the hex field
    And selects a blue color from the color picker
    Then the hex field should update to the corresponding hex value (e.g., "#0000FF")
    And the preview should update to show blue header text

  Scenario: Color picker reflects current hex value
    Given the "Agent interface header text color" field contains "#00FF00"
    When the user opens the color picker
    Then the color picker should display green as the selected color

# ==========================================
# VALIDATION & NEGATIVE SCENARIOS
# ==========================================

  Scenario: Reject invalid hex format with special characters
    Given the "Agent interface header text color" field contains "#FFFFFF"
    When the user enters "GGG123" in the field
    And attempts to save
    Then system should retain old value
    And the setting should not be saved

  Scenario: Reject hex value without hash prefix
    When the user enters "FF5733" (without #) in the field
    And attempts to save
    Then system should retain old value

  Scenario: Reject empty value
    Given the "Agent interface header text color" field is mandatory
    When the user clears the field
    And attempts to save
    Then system should retain old value
    And the setting should not be saved

  Scenario: Reject hex value with too many characters
    When the user enters "#FF5733FF00" in the field
    And attempts to save
    Then system should retain old value

  Scenario: Cancel discards color changes
    Given the "Agent interface header text color" field displays "#FFFFFF"
    And the user changes the value to "#FF0000"
    When the user clicks the "Cancel" button
    Then the changes should be discarded
    And the field should revert to "#FFFFFF"
    And the agent interface header text should remain white

# ==========================================
# 3-DIGIT SHORTHAND HEX SCENARIOS
# ==========================================

  Scenario: Accept 3-digit shorthand hex value
    When the user enters "#F00" in the field
    And saves the settings
    Then the system should normalize it to "#FF0000"
    And the header text should display in red color

  Scenario: Accept 3-digit shorthand for white
    When the user enters "#FFF" in the field
    And saves the settings
    Then the header text should display in white color

# ==========================================
# PREVIEW MODE SCENARIOS
# ==========================================

  Scenario: Real-time preview of color change
    Given the user is in preview mode
    When the user changes "Agent interface header text color" to "#00FF00"
    Then the preview should immediately update to show green header text
    Before clicking the Save button

  Scenario: Preview reflects saved color after re-entry
    Given the user previously saved "#123456" as the header text color
    When the user navigates away and returns to Theme Settings
    Then the preview should show header text in color #123456
    And the hex field should display "#123456"

# ==========================================
# ACCESSIBILITY & CONTRAST SCENARIOS
# ==========================================

  # Scenario: Warning for low contrast combination
  #   Given the "Agent interface header background" is "#000000" (black)
  #   When the user sets "Agent interface header text color" to "#000000" (black)
  #   Then the system should display a warning about low contrast
    # Inference (low confidence): Contrast warning may not be implemented

  # Scenario: Sufficient contrast passes without warning
  #   Given the "Agent interface header background" is "#00264B" (dark blue)
  #   When the user sets "Agent interface header text color" to "#FFFFFF" (white)
  #   Then no contrast warning should be displayed
  #   And the text should be clearly readable

# ==========================================
# UPGRADE SCENARIOS (Version 26.2)
# ==========================================

  Scenario: New field appears after upgrade from pre-26.2
    Given the system was upgraded from version 26.1 to 26.2
    And a theme "PreUpgrade Theme" existed before the upgrade
    When the user opens "PreUpgrade Theme" in Theme Settings
    Then the "Agent interface header text color" field should be present
    And the field should contain the default value "#FFFFFF"
    And previously customized header colors should remain unchanged

  Scenario: Default behavior after upgrade before configuration
    Given the system was upgraded to version 26.2
    And no user has modified the "Agent interface header text color" setting
    When an agent user logs into the agent interface
    Then the header text should display in white color (matching #FFFFFF default)
    And there should be no visual regression from the previous version

  Scenario: Upgrade does not break existing themes
    Given the system was upgraded to version 26.2
    And "Corporate Theme" had custom header styling in version 26.1
    When the user views the agent interface with "Corporate Theme" applied
    Then the header text should maintain white color as before upgrade

# ==========================================
# CROSS-THEME & PERSISTENCE SCENARIOS
# ==========================================

  Scenario Outline: Selected header text color is visible across agent portal navigation
    Given the user is in "Theme Settings"
    And the user sets "Agent interface header text color" to "#FF5733"
    When the user clicks the "Save" button
    And the user navigates to "<NavigationPath>"
    Then the agent interface header text should display in color "#FF5733"

    Examples:
      | NavigationPath                                  |
      | agent portal -> dashboard                       |
      | agent portal -> design                          |
      | agent portal -> audit                           |
      | agent portal -> operation orchestrations        |

  Scenario: Color setting persists per theme
    Given "Theme A" has header text color set to "#FF0000"
    And "Theme B" has header text color set to "#00FF00"
    When the user switches from "Theme A" to "Theme B"
    Then the "Agent interface header text color" field should display "#00FF00"
    And when switching back to "Theme A"
    Then the field should display "#FF0000"

  Scenario: Color applies only to agent interface header
    Given the "Agent interface header text color" is set to "#FF00FF" (magenta)
    When the user views the agent interface
    Then only the header text should be magenta
    And other page text elements should maintain their theme colors
    And the Service Portal header should not be affected

# ==========================================
# BROWSER & DEVICE SCENARIOS
# ==========================================

  Scenario: Color displays correctly across browsers
    Given "Agent interface header text color" is set to "#4A90E2"
    When the agent interface is viewed in Chrome, Firefox, Edge, and Safari
    Then the header text should display the same blue color (#4A90E2) in all browsers

  Scenario: Color displays correctly on different screen resolutions
    Given "Agent interface header text color" is set to "#7B68EE"
    When the agent interface is viewed on desktop, tablet, and mobile devices
    Then the header text should maintain the medium slate blue color consistently