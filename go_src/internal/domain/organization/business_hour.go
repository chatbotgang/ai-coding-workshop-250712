package organization

import "time"

// Weekday represents the days of the week for business hours.
type Weekday int

const (
	Monday Weekday = iota + 1
	Tuesday
	Wednesday
	Thursday
	Friday
	Saturday
	Sunday
)

// BusinessHour represents the business hours configuration for an organization.
// It defines when the organization is available for business operations.
type BusinessHour struct {
	ID             int       `json:"id"`
	OrganizationID string    `json:"organization_id"`
	Weekday        Weekday   `json:"weekday"`
	StartTime      time.Time `json:"start_time"`
	EndTime        time.Time `json:"end_time"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}
