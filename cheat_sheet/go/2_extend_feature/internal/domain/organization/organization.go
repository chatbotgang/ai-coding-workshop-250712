package organization

import (
	"time"
)

// LanguageCode represents supported language codes.
type LanguageCode string

const (
	LanguageCodeZhHant LanguageCode = "zh-hant"
	LanguageCodeZhHans LanguageCode = "zh-hans"
	LanguageCodeEn     LanguageCode = "en"
	// Add more language codes as needed
)

// Organization represents an organization entity in the system.
// It contains the core business information and settings for an organization.
type Organization struct {
	ID              int          `json:"id"`
	Name            string       `json:"name"`
	UUID            string       `json:"uuid"`
	PlanID          *string      `json:"plan_id,omitempty"`
	EnableTwoFactor bool         `json:"enable_two_factor"`
	Timezone        string       `json:"timezone"`
	LanguageCode    LanguageCode `json:"language_code"`
	Enable          bool         `json:"enable"`
	CreatedAt       time.Time    `json:"created_at"`
	UpdatedAt       time.Time    `json:"updated_at"`
	ExpiredAt       *time.Time   `json:"expired_at,omitempty"`
}
