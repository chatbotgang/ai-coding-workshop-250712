package organization

import (
	"time"
)

// Bot represents a channel entity associated with an organization.
// It contains the configuration and credentials for integration across multiple platforms (LINE, Facebook, Instagram).
type Bot struct {
	ID               int        `json:"id"`
	OrganizationID   int        `json:"organization_id"`
	Name             string     `json:"name"`
	Type             BotType    `json:"type"`
	ChannelID        string     `json:"channel_id"`
	ChannelSecret    string     `json:"channel_secret"`
	AccessToken      string     `json:"access_token"`
	TokenExpiredTime time.Time  `json:"token_expired_time"`
	CreatedAt        time.Time  `json:"created_at"`
	UpdatedAt        time.Time  `json:"updated_at"`
	ExpiredAt        *time.Time `json:"expired_at,omitempty"`
	Enable           bool       `json:"enable"`
}

// BotType represents the type of bot.
type BotType string

const (
	BotTypeLine      BotType = "LINE"
	BotTypeFacebook  BotType = "FB"
	BotTypeInstagram BotType = "IG"
	// Add other bot types as needed
)

// IsActive returns true if the bot is enabled and not expired.
func (b *Bot) IsActive() bool {
	if !b.Enable {
		return false
	}
	if b.ExpiredAt != nil && time.Now().After(*b.ExpiredAt) {
		return false
	}
	return true
}

// IsTokenExpired returns true if the bot's access token has expired.
func (b *Bot) IsTokenExpired() bool {
	return b.TokenExpiredTime.Before(time.Now())
}

// IsTokenValid returns true if the bot has a valid access token.
func (b *Bot) IsTokenValid() bool {
	return b.AccessToken != "" && !b.IsTokenExpired()
}
