# Organization

## Feature Overview
- **Purpose:** Provides multi-tenant infrastructure for managing organizations, their plans, feature settings, and user access within the Rubato platform
- **Main Use Cases:** 
  - Organization creation and management
  - Plan and feature setting management based on subscription tiers
  - Organization-specific feature access control
  - User-organization association and switching

## Major Workflows

### Organization Creation and Management
1. **Create Organization**: Organizations are created with a unique name, UUID, and optional plan
   - [organization/models.py:Organization](../organization/models.py#L22)
2. **Update Organization**: Organizations can be updated with new properties
   - [organization/services/organization.py:UpdateOrganizationService.execute](../organization/services/organization.py#L110)
3. **Retrieve Organization**: Get organization details by ID
   - [organization/services/organization.py:GetOrganizationService.execute](../organization/services/organization.py#L100)
4. **List Organizations**: Get all organizations or organizations a user has access to
   - [organization/views.py:OrganizationViewSet.list](../organization/views.py#L111)
   - [organization/services/organization.py:GetUserAvailableOrganizationsService.execute](../organization/services/organization.py#L165)

### Feature Setting Management
1. **Get Feature Settings**: Retrieve feature settings for an organization based on its plan
   - [organization/services/feature_setting.py:ListFeatureSettingsServices.execute](../organization/services/feature_setting.py#L28)
   - [organization/views.py:OrganizationViewSet.feature_settings](../organization/views.py#L191)
2. **Override Feature Settings**: Custom feature settings can be applied to specific organizations through the admin interface
   - [organization/models.py:OverrideFeatureSetting](../organization/models.py#L198)
3. **Validate Feature Operations**: Check if an organization can perform operations based on its feature settings
   - [organization/services/feature_setting.py:ValidateOperationByFeatureSettingService.execute](../organization/services/feature_setting.py#L135)
4. **Sync Predefined Plans**: Admin action to update plan feature settings from code constants
   - [organization/services/plan.py:SyncPredefinedPlansService.execute](../organization/services/plan.py#L11)
   - [organization/admin.py:PlanAdmin.sync_predefined_plans](../organization/admin.py#L300)

### User Organization Management
1. **Switch Organization**: Allow users to switch between organizations they have access to
   - [organization/services/organization.py:SwitchUserOrganizationService.execute](../organization/services/organization.py#L195)
   - [organization/views.py:OrganizationViewSet.switch](../organization/views.py#L356)
2. **Get User's Available Organizations**: List all organizations a user has access to
   - [organization/services/organization.py:GetUserAvailableOrganizationsService.execute](../organization/services/organization.py#L165)

### Organization Offboarding
1. **Offboard Organization**: Disable bots, webhooks, and reset settings for an organization
   - [organization/services/organization.py:OffboardOrganizationService.execute](../organization/services/organization.py#L62)

## Key Data Models and Contracts

### Core Models
- **Organization**: Core entity representing a tenant in the system
  ```python
  class Organization(models.Model):
      name = models.CharField(max_length=255, unique=True)
      uuid = models.CharField(max_length=36, unique=True, default=uuid.uuid4)
      url_namespace = models.CharField(max_length=5, blank=True, null=True)
      plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
      enable_two_factor = models.BooleanField(default=True)
      timezone = models.CharField(
          max_length=63,
          blank=True,
          null=True,
          default="Asia/Taipei",
          choices=[(tz, tz) for tz in pytz.common_timezones],
          help_text="Timezone for the organization, e.g., Asia/Taipei",
      )
  [organization/models.py:Organization](../organization/models.py#L22)

- **Plan**: Subscription plan that determines feature access
  ```python
  class Plan(models.Model):
      name = models.CharField(max_length=64, unique=True)
      is_custom = models.BooleanField(default=False)
      description = models.TextField(null=True, blank=True)
  ```
  [organization/models.py:Plan](../organization/models.py#L11)

- **FeatureSetting**: Defines feature access levels for plans
  ```python
  class FeatureSetting(AbstractFeatureSetting):
      setting_code = models.CharField(max_length=256, choices=[(code.value, code.value) for code in FeatureSettingCode])
      level = models.CharField(max_length=128)
  ```
  [organization/models.py:FeatureSetting](../organization/models.py#L179)

- **OverrideFeatureSetting**: Custom feature settings for specific organizations
  ```python
  class OverrideFeatureSetting(AbstractFeatureSetting):
      organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
  ```
  [organization/models.py:OverrideFeatureSetting](../organization/models.py#L198)

- **PlanFeatureSettingBundle**: Links plans to their feature settings
  ```python
  class PlanFeatureSettingBundle(models.Model):
      plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
      feature = models.ForeignKey(FeatureSetting, on_delete=models.CASCADE)
  ```
  [organization/models.py:PlanFeatureSettingBundle](../organization/models.py#L187)

### Feature Setting Constants
- **DEFAULT_PLAN_FEATURE_SETTING_BUNDLE**: Defines template feature settings for each predefined plan
  [organization/constants.py:DEFAULT_PLAN_FEATURE_SETTING_BUNDLE](../organization/constants.py#L250)

- **old_plan_default_feature_settings**: Default settings for legacy organizations without a plan
  [organization/domains/feature_setting.py:old_plan_default_feature_settings](../organization/domains/feature_setting.py#L460)


## Edge Cases & Constraints

- **Organization Name Uniqueness**: Organization names must be unique
  - Handled by database constraint and checked by [organization/services/organization.py:CheckOrganizationNameExistService](../organization/services/organization.py#L23)

- **Feature Setting Inheritance**: Organizations inherit settings from their plan, but can have overrides
  - [organization/services/feature_setting.py:ListFeatureSettingsServices.execute](../organization/services/feature_setting.py#L28)
  - Overrides take precedence over plan settings

- **Organization Offboarding Constraints**: Only organizations with one bot can be offboarded
  - [organization/services/organization.py:OffboardOrganizationService.execute](../organization/services/organization.py#L70)
  ```python
  if len(bots) > 1:
      # to avoid ambiguity, we only process the organization with one enabled bot
      raise Exception("organization has more than one bot")
  ```

- **Feature Setting Validation**: Operations are validated against feature settings
  - [organization/services/feature_setting.py:ValidateOperationByFeatureSettingService](../organization/services/feature_setting.py#L119)
  - Prevents organizations from using features not included in their plan
  - Validation errors are clearly communicated to users

- **Legacy Organizations**: Organizations without a plan use default feature settings
  - [organization/services/feature_setting.py:ListOldPlanFeatureSettingsServices](../organization/services/feature_setting.py#L64)
  - Uses `old_plan_default_feature_settings` for basic functionality

## Known Technical Traps

- **Plan vs. Feature Settings**: Organizations without a plan use old_plan_default_feature_settings
  - [organization/services/feature_setting.py:ListOldPlanFeatureSettingsServices.execute](../organization/services/feature_setting.py#L75)
  - This dual system (plan-based vs. legacy) can cause confusion

- **Feature Setting Visibility Control**: Not all feature settings are exposed via API
  - [organization/constants.py:FeatureSettingCode.public_setting_codes](../organization/constants.py#L51)
  - Only settings in this list are returned by the API

- **Organization Switching with Admin Center**: Feature toggle controls whether users are synced to Admin Center
  - [organization/services/organization.py:SwitchUserOrganizationService.execute](../organization/services/organization.py#L205)
  - If the feature is enabled but Admin Center sync fails, the user might be in an inconsistent state

- **Namespace Regex Validation**: URL namespace has a specific regex pattern that must be followed
  - [organization/models.py:Organization.NAMESPACE_REGEX](../organization/models.py#L23)
  - `"[0-9a-z_]{1,5}"` - only numbers, lowercase letters, or underscores, max 5 chars

- **Feature Setting Overrides**: Overrides can only be created through the Django admin interface
  - [organization/models.py:OverrideFeatureSetting](../organization/models.py#L198)
  - No self-service option for organization admins

## Test Coverage

- Organization model tests: [organization/tests/test_models.py](../organization/tests/test_models.py)
- Organization service tests: [organization/tests/test_services.py](../organization/tests/test_services.py)
- Feature setting tests: [organization/tests/test_feature_settings.py](../organization/tests/test_feature_settings.py)
- API endpoint tests: [organization/tests/test_views.py](../organization/tests/test_views.py)

## How to Extend/Debug

### Adding a New Feature Setting
1. Add new setting code to `FeatureSettingCode` enum in [organization/constants.py](../organization/constants.py)
2. Create a new level class for the setting (e.g., `NewFeatureLevel`)
3. Add the setting to `public_setting_codes()` method to expose it via API
4. Update plan default settings in `DEFAULT_PLAN_FEATURE_SETTING_BUNDLE`
5. Run the `sync_predefined_plans` admin action to update the database

### Debugging Common Issues
- **Feature Access Issues**: Check if the organization has the required feature setting level
  - Use `ValidateOperationByFeatureSettingService` to validate operations
  - Check for override settings in the admin panel
  - Look for clear error messages from `FeatureSettingLevelNotAllowedError`
- **Organization Switching Problems**: 
  - Verify user membership in the organization
  - Check if Admin Center sync is enabled and working properly
  - Look for JWT token generation issues
- **Plan Changes**: 
  - Verify that the plan was properly updated in the admin interface
  - Check if feature settings were properly synced using the admin action

## Known TODOs/Technical Debt

- URL namespace is marked as deprecated in the model but still used in code
  - [organization/models.py:Organization.url_namespace](../organization/models.py#L26)
- Dual feature setting system (plan-based vs. legacy) needs consolidation
- Error handling in organization offboarding could be improved
- Some hard-coded values in feature setting levels (e.g., unlimited thresholds)
- No self-service option for organizations to upgrade their plans
- Manual process required to sync feature settings when code constants change

## Related Features/Modules

- **User Management**: Handles user creation and authentication
- **Bot Management**: Bots are associated with organizations
- **Webhook System**: Webhooks are tied to bots and affected by organization offboarding
- **Admin Center Integration**: Used for user-organization management
- **Feature Toggle System**: Controls behavior like Admin Center integration
