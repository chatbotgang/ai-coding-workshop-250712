package auto_reply

import (
	"context"
	"time"
)

// AutoReply represents an omnichannel rule that associates several WebhookTriggerSetting instances.
// It defines the high-level auto-reply configuration for an organization.
type AutoReply struct {
	ID                      int                             `json:"id"`
	OrganizationID          int                             `json:"organization_id"`
	Name                    string                          `json:"name"`
	Status                  AutoReplyStatus                 `json:"status"`
	EventType               AutoReplyEventType              `json:"event_type"`
	Priority                int                             `json:"priority"`
	Keywords                []string                        `json:"keywords,omitempty"`
	TriggerScheduleType     *WebhookTriggerScheduleType     `json:"trigger_schedule_type,omitempty"`
	TriggerScheduleSettings *WebhookTriggerScheduleSettings `json:"trigger_schedule_settings,omitempty"`
	CreatedAt               time.Time                       `json:"created_at"`
	UpdatedAt               time.Time                       `json:"updated_at"`
}

// AutoReplyStatus represents the status of an auto-reply rule.
type AutoReplyStatus string

const (
	AutoReplyStatusActive   AutoReplyStatus = "active"
	AutoReplyStatusInactive AutoReplyStatus = "inactive"
	AutoReplyStatusArchived AutoReplyStatus = "archived"
)

// AutoReplyEventType represents the type of event that triggers the auto-reply.
type AutoReplyEventType string

const (
	AutoReplyEventTypeMessage  AutoReplyEventType = "message"
	AutoReplyEventTypePostback AutoReplyEventType = "postback"
	AutoReplyEventTypeFollow   AutoReplyEventType = "follow"
	AutoReplyEventTypeBeacon   AutoReplyEventType = "beacon"
	AutoReplyEventTypeTime     AutoReplyEventType = "time"
	AutoReplyEventTypeKeyword  AutoReplyEventType = "keyword"
	AutoReplyEventTypeDefault  AutoReplyEventType = "default"
)

// AutoReplyRepository defines the interface for persisting AutoReply settings.
type AutoReplyRepository interface {
	Create(ctx context.Context, ar *AutoReply) error
	Update(ctx context.Context, ar *AutoReply) error
	Delete(ctx context.Context, id int) error
	GetByID(ctx context.Context, id int) (*AutoReply, error)
	ListByOrganization(ctx context.Context, orgID int) ([]*AutoReply, error)
}
