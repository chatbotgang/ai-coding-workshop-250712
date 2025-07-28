package autoreply

import (
	"context"

	"github.com/chatbotgang/workshop/internal/domain/auto_reply"
	"github.com/chatbotgang/workshop/internal/domain/organization"
)

// AutoReplyRepository defines the interface for fetching auto-reply trigger settings.
type AutoReplyRepository interface {
	ListTriggerSettings(ctx context.Context, botID int) ([]*auto_reply.AutoReplyTriggerSetting, error)
}

// BusinessHourRepository defines the interface for fetching business hours.
type BusinessHourRepository interface {
	ListBusinessHours(ctx context.Context, orgID int) ([]organization.BusinessHour, error)
}

// BotRepository defines the interface for fetching bot/channel info (for timezone, orgID, etc.).
type BotRepository interface {
	GetBot(ctx context.Context, botID int) (*organization.Bot, error)
}

// OrganizationRepository defines the interface for fetching organization info (for timezone, etc.).
type OrganizationRepository interface {
	GetOrganization(ctx context.Context, orgID int) (*organization.Organization, error)
}

// AutoReplyService defines the application service interface for auto-reply trigger validation.
type AutoReplyService interface {
	FindMatchingTrigger(ctx context.Context, event auto_reply.WebhookEvent, botID int) (*auto_reply.AutoReplyTriggerSetting, error)
}

// autoReplyService is the concrete implementation of AutoReplyService.
type autoReplyService struct {
	autoReplyRepo    AutoReplyRepository
	businessHourRepo BusinessHourRepository
	botRepo          BotRepository
	organizationRepo OrganizationRepository
}

// AutoReplyServiceParam is the parameter struct for constructing autoReplyService.
type AutoReplyServiceParam struct {
	AutoReplyRepo    AutoReplyRepository
	BusinessHourRepo BusinessHourRepository
	BotRepo          BotRepository
	OrganizationRepo OrganizationRepository
}

// NewAutoReplyService constructs a new AutoReplyService.
func NewAutoReplyService(param AutoReplyServiceParam) AutoReplyService {
	return &autoReplyService{
		autoReplyRepo:    param.AutoReplyRepo,
		businessHourRepo: param.BusinessHourRepo,
		botRepo:          param.BotRepo,
		organizationRepo: param.OrganizationRepo,
	}
}

// FindMatchingTrigger orchestrates domain logic to find the first matching auto-reply trigger for the event.
func (s *autoReplyService) FindMatchingTrigger(ctx context.Context, event auto_reply.WebhookEvent, botID int) (*auto_reply.AutoReplyTriggerSetting, error) {
	// 1. 取得 bot/channel 資訊（含 orgID）
	bot, err := s.botRepo.GetBot(ctx, botID)
	if err != nil {
		return nil, err
	}
	// 2. 取得 organization 資訊（含 timezone）
	org, err := s.organizationRepo.GetOrganization(ctx, bot.OrganizationID)
	if err != nil {
		return nil, err
	}
	// 3. 取得 auto-reply trigger settings
	triggers, err := s.autoReplyRepo.ListTriggerSettings(ctx, botID)
	if err != nil {
		return nil, err
	}
	// 4. 取得 business hours
	businessHours, err := s.businessHourRepo.ListBusinessHours(ctx, bot.OrganizationID)
	if err != nil {
		return nil, err
	}
	// 5. 組 aggregate
	agg := &auto_reply.AutoReplyChannelSettingAggregate{
		BotID:           botID,
		TriggerSettings: triggers,
		BusinessHours:   businessHours,
		Timezone:        org.Timezone,
	}
	// 6. 調用 domain 聚合進行驗證
	return agg.ValidateTrigger(event)
}
