package auto_reply

import (
	"encoding/json"
	"time"
)

// ScheduleValidator handles time-based trigger validation logic.
type ScheduleValidator struct{}

// NewScheduleValidator creates a new ScheduleValidator instance.
func NewScheduleValidator() *ScheduleValidator {
	return &ScheduleValidator{}
}

// ScheduleValidationResult represents the result of schedule validation.
type ScheduleValidationResult struct {
	IsMatch      bool   `json:"is_match"`
	Reason       string `json:"reason,omitempty"`
	ScheduleType string `json:"schedule_type,omitempty"`
}

// ValidateSchedule validates if the current time matches the trigger schedule.
// Implements the priority system from the Feature KB:
// 1. MONTHLY (highest priority)
// 2. BUSINESS_HOUR
// 3. NON_BUSINESS_HOUR  
// 4. DAILY (lowest priority)
func (sv *ScheduleValidator) ValidateSchedule(
	autoReply *AutoReply,
	eventTime time.Time,
	businessHours []*BusinessHour,
	timezone *time.Location,
) *ScheduleValidationResult {
	if autoReply.TriggerScheduleType == nil {
		return &ScheduleValidationResult{
			IsMatch: false,
			Reason:  "no schedule type configured",
		}
	}

	scheduleType := *autoReply.TriggerScheduleType

	switch scheduleType {
	case WebhookTriggerScheduleTypeMonthly:
		// Convert event time to the specified timezone for monthly/daily schedules
		if timezone != nil {
			eventTime = eventTime.In(timezone)
		}
		return sv.validateMonthlySchedule(autoReply, eventTime)
	case WebhookTriggerScheduleTypeBusinessHour:
		return sv.validateBusinessHourSchedule(eventTime, businessHours, timezone)
	case WebhookTriggerScheduleTypeNonBusinessHour:
		return sv.validateNonBusinessHourSchedule(eventTime, businessHours, timezone)
	case WebhookTriggerScheduleTypeDaily:
		// Convert event time to the specified timezone for monthly/daily schedules
		if timezone != nil {
			eventTime = eventTime.In(timezone)
		}
		return sv.validateDailySchedule(autoReply, eventTime)
	case WebhookTriggerScheduleTypeDateRange:
		// Convert event time to the specified timezone for monthly/daily schedules
		if timezone != nil {
			eventTime = eventTime.In(timezone)
		}
		return sv.validateDateRangeSchedule(autoReply, eventTime)
	default:
		return &ScheduleValidationResult{
			IsMatch: false,
			Reason:  "unsupported schedule type: " + string(scheduleType),
		}
	}
}

// validateMonthlySchedule validates monthly schedule triggers.
func (sv *ScheduleValidator) validateMonthlySchedule(autoReply *AutoReply, eventTime time.Time) *ScheduleValidationResult {
	if autoReply.TriggerScheduleSettings == nil {
		return &ScheduleValidationResult{
			IsMatch: false,
			Reason:  "no monthly schedule settings configured",
		}
	}

	var schedules []MonthlySchedule
	for _, schedule := range autoReply.TriggerScheduleSettings.Schedules {
		if schedule.GetScheduleType() == WebhookTriggerScheduleTypeMonthly {
			var monthlySchedule MonthlySchedule
			if err := json.Unmarshal(schedule.GetScheduleSettings(), &monthlySchedule); err != nil {
				continue
			}
			schedules = append(schedules, monthlySchedule)
		}
	}

	currentDay := eventTime.Day()
	currentTime := eventTime

	for _, schedule := range schedules {
		if schedule.Day == currentDay {
			if sv.isTimeInRange(currentTime, schedule.StartTime, schedule.EndTime) {
				return &ScheduleValidationResult{
					IsMatch:      true,
					ScheduleType: string(WebhookTriggerScheduleTypeMonthly),
				}
			}
		}
	}

	return &ScheduleValidationResult{
		IsMatch: false,
		Reason:  "current time does not match monthly schedule",
	}
}

// validateBusinessHourSchedule validates business hour schedule triggers.
func (sv *ScheduleValidator) validateBusinessHourSchedule(eventTime time.Time, businessHours []*BusinessHour, timezone *time.Location) *ScheduleValidationResult {
	if len(businessHours) == 0 {
		return &ScheduleValidationResult{
			IsMatch: false,
			Reason:  "no business hours configured",
		}
	}

	// Convert event time to UTC for business hour comparison (business hours are stored in UTC)
	utcTime := eventTime.In(time.UTC)

	// Go's weekday: Sunday=0, Monday=1, Tuesday=2, ..., Saturday=6
	// Our BusinessHour weekday: Monday=1, Tuesday=2, ..., Sunday=7
	currentWeekday := int(utcTime.Weekday())
	if currentWeekday == 0 { // Convert Sunday from 0 to 7
		currentWeekday = 7
	}

	for _, bh := range businessHours {
		if bh.Weekday == currentWeekday {
			if sv.isTimeInBusinessHourRange(utcTime, bh) {
				return &ScheduleValidationResult{
					IsMatch:      true,
					ScheduleType: string(WebhookTriggerScheduleTypeBusinessHour),
				}
			}
		}
	}

	return &ScheduleValidationResult{
		IsMatch: false,
		Reason:  "current time is not within business hours",
	}
}

// validateNonBusinessHourSchedule validates non-business hour schedule triggers.
func (sv *ScheduleValidator) validateNonBusinessHourSchedule(eventTime time.Time, businessHours []*BusinessHour, timezone *time.Location) *ScheduleValidationResult {
	// Non-business hour is the inverse of business hour
	businessResult := sv.validateBusinessHourSchedule(eventTime, businessHours, timezone)
	
	if businessResult.IsMatch {
		return &ScheduleValidationResult{
			IsMatch: false,
			Reason:  "current time is within business hours",
		}
	}

	return &ScheduleValidationResult{
		IsMatch:      true,
		ScheduleType: string(WebhookTriggerScheduleTypeNonBusinessHour),
	}
}

// validateDailySchedule validates daily schedule triggers.
func (sv *ScheduleValidator) validateDailySchedule(autoReply *AutoReply, eventTime time.Time) *ScheduleValidationResult {
	if autoReply.TriggerScheduleSettings == nil {
		return &ScheduleValidationResult{
			IsMatch: false,
			Reason:  "no daily schedule settings configured",
		}
	}

	var schedules []DailySchedule
	for _, schedule := range autoReply.TriggerScheduleSettings.Schedules {
		if schedule.GetScheduleType() == WebhookTriggerScheduleTypeDaily {
			var dailySchedule DailySchedule
			if err := json.Unmarshal(schedule.GetScheduleSettings(), &dailySchedule); err != nil {
				continue
			}
			schedules = append(schedules, dailySchedule)
		}
	}

	for _, schedule := range schedules {
		if sv.isTimeInDailyRange(eventTime, schedule.StartTime, schedule.EndTime) {
			return &ScheduleValidationResult{
				IsMatch:      true,
				ScheduleType: string(WebhookTriggerScheduleTypeDaily),
			}
		}
	}

	return &ScheduleValidationResult{
		IsMatch: false,
		Reason:  "current time does not match daily schedule",
	}
}

// validateDateRangeSchedule validates date range schedule triggers.
func (sv *ScheduleValidator) validateDateRangeSchedule(autoReply *AutoReply, eventTime time.Time) *ScheduleValidationResult {
	if autoReply.TriggerScheduleSettings == nil {
		return &ScheduleValidationResult{
			IsMatch: false,
			Reason:  "no date range schedule settings configured",
		}
	}

	var schedules []DateRangeSchedule
	for _, schedule := range autoReply.TriggerScheduleSettings.Schedules {
		if schedule.GetScheduleType() == WebhookTriggerScheduleTypeDateRange {
			var dateRangeSchedule DateRangeSchedule
			if err := json.Unmarshal(schedule.GetScheduleSettings(), &dateRangeSchedule); err != nil {
				continue
			}
			schedules = append(schedules, dateRangeSchedule)
		}
	}

	currentDate := eventTime.Format("2006-01-02")

	for _, schedule := range schedules {
		if currentDate >= schedule.StartDate && currentDate <= schedule.EndDate {
			return &ScheduleValidationResult{
				IsMatch:      true,
				ScheduleType: string(WebhookTriggerScheduleTypeDateRange),
			}
		}
	}

	return &ScheduleValidationResult{
		IsMatch: false,
		Reason:  "current date does not fall within date range",
	}
}

// isTimeInRange checks if the current time falls within the specified time range.
// Handles time ranges within the same day.
func (sv *ScheduleValidator) isTimeInRange(currentTime time.Time, startTime, endTime string) bool {
	start, err := time.Parse("15:04", startTime)
	if err != nil {
		return false
	}
	
	end, err := time.Parse("15:04", endTime)
	if err != nil {
		return false
	}

	// Create time objects for comparison on the same date
	currentHour := currentTime.Hour()
	currentMinute := currentTime.Minute()
	current := time.Date(0, 1, 1, currentHour, currentMinute, 0, 0, time.UTC)
	
	startOfDay := time.Date(0, 1, 1, start.Hour(), start.Minute(), 0, 0, time.UTC)
	endOfDay := time.Date(0, 1, 1, end.Hour(), end.Minute(), 59, 999999999, time.UTC)

	return (current.After(startOfDay) || current.Equal(startOfDay)) && current.Before(endOfDay)
}

// isTimeInDailyRange checks if the current time falls within the daily schedule range.
// Supports midnight crossing ranges (e.g., 22:00 to 06:00).
func (sv *ScheduleValidator) isTimeInDailyRange(currentTime time.Time, startTime, endTime string) bool {
	start, err := time.Parse("15:04", startTime)
	if err != nil {
		return false
	}
	
	end, err := time.Parse("15:04", endTime)
	if err != nil {
		return false
	}

	currentHour := currentTime.Hour()
	currentMinute := currentTime.Minute()
	currentSeconds := currentTime.Second()
	current := time.Date(0, 1, 1, currentHour, currentMinute, currentSeconds, 0, time.UTC)
	
	startOfDay := time.Date(0, 1, 1, start.Hour(), start.Minute(), 0, 0, time.UTC)
	endOfDay := time.Date(0, 1, 1, end.Hour(), end.Minute(), 0, 0, time.UTC)

	// Check for midnight crossing
	if start.After(end) {
		// Range crosses midnight (e.g., 22:00 to 06:00)
		// Match if current time is >= start time OR < end time
		return (current.After(startOfDay) || current.Equal(startOfDay)) || current.Before(endOfDay)
	}

	// Normal range within the same day
	// Match if current time is >= start time AND < end time
	return (current.After(startOfDay) || current.Equal(startOfDay)) && current.Before(endOfDay)
}

// isTimeInBusinessHourRange checks if the current time falls within business hour range.
func (sv *ScheduleValidator) isTimeInBusinessHourRange(currentTime time.Time, businessHour *BusinessHour) bool {
	// Extract time components for comparison
	currentHour := currentTime.Hour()
	currentMinute := currentTime.Minute()
	current := time.Date(0, 1, 1, currentHour, currentMinute, 0, 0, time.UTC)
	
	start := time.Date(0, 1, 1, businessHour.StartTime.Hour(), businessHour.StartTime.Minute(), 0, 0, time.UTC)
	end := time.Date(0, 1, 1, businessHour.EndTime.Hour(), businessHour.EndTime.Minute(), 59, 999999999, time.UTC)

	return (current.After(start) || current.Equal(start)) && current.Before(end)
}