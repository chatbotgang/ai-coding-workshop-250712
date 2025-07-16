package auto_reply

import (
	"time"
)

// BotType represents the type of bot/channel.
type BotType string

const (
	BotTypeLine      BotType = "LINE"
	BotTypeFacebook  BotType = "FB" 
	BotTypeInstagram BotType = "IG"
)

// WebhookEvent represents a normalized webhook event from any channel (LINE, Facebook, Instagram).
type WebhookEvent struct {
	ID            string                  `json:"id"`
	EventType     WebhookEventType        `json:"event_type"`
	ChannelType   BotType                 `json:"channel_type"`
	BotID         int                     `json:"bot_id"`
	UserID        string                  `json:"user_id"`
	MessageText   string                  `json:"message_text,omitempty"`
	IGStoryID     *string                 `json:"ig_story_id,omitempty"`   // Instagram Story context
	PostbackData  *string                 `json:"postback_data,omitempty"` // For postback events
	BeaconData    *string                 `json:"beacon_data,omitempty"`   // For beacon events
	Timestamp     time.Time               `json:"timestamp"`
	ReplyToken    *string                 `json:"reply_token,omitempty"` // Platform-specific reply token
	Extra         map[string]any          `json:"extra,omitempty"`       // Platform-specific additional data
}

// WebhookEventType represents the type of webhook event.
type WebhookEventType string

const (
	WebhookEventTypeMessage  WebhookEventType = "message"
	WebhookEventTypePostback WebhookEventType = "postback"
	WebhookEventTypeFollow   WebhookEventType = "follow"
	WebhookEventTypeBeacon   WebhookEventType = "beacon"
	WebhookEventTypeTime     WebhookEventType = "time" // For time-based triggers
)

// IsIGStoryReply returns true if this event is a reply to an Instagram Story.
func (w *WebhookEvent) IsIGStoryReply() bool {
	return w.ChannelType == BotTypeInstagram && w.IGStoryID != nil && *w.IGStoryID != ""
}

// IsMessageEvent returns true if this is a message-type event.
func (w *WebhookEvent) IsMessageEvent() bool {
	return w.EventType == WebhookEventTypeMessage
}

// GetNormalizedMessageText returns the message text with normalization for keyword matching.
// - Trims leading and trailing whitespace
// - Converts to lowercase for case-insensitive matching
func (w *WebhookEvent) GetNormalizedMessageText() string {
	if w.MessageText == "" {
		return ""
	}
	// Note: Normalization is done in the keyword matcher to maintain original text
	return w.MessageText
}

// SupportsKeywordTriggers returns true if this event type supports keyword-based triggers.
func (w *WebhookEvent) SupportsKeywordTriggers() bool {
	switch w.EventType {
	case WebhookEventTypeMessage, WebhookEventTypePostback, WebhookEventTypeBeacon:
		return true
	default:
		return false
	}
}