package autoreply

import (
	"context"
	"testing"
	"time"

	"github.com/chatbotgang/workshop/internal/domain/auto_reply"
	"github.com/chatbotgang/workshop/internal/domain/organization"
)

type mockAutoReplyRepo struct {
	triggers []*auto_reply.AutoReplyTriggerSetting
}

func (m *mockAutoReplyRepo) ListTriggerSettings(ctx context.Context, botID int) ([]*auto_reply.AutoReplyTriggerSetting, error) {
	return m.triggers, nil
}

type mockBusinessHourRepo struct {
	hours []organization.BusinessHour
}

func (m *mockBusinessHourRepo) ListBusinessHours(ctx context.Context, orgID int) ([]organization.BusinessHour, error) {
	return m.hours, nil
}

type mockBotRepo struct {
	bot *organization.Bot
}

func (m *mockBotRepo) GetBot(ctx context.Context, botID int) (*organization.Bot, error) {
	return m.bot, nil
}

type mockOrgRepo struct {
	org *organization.Organization
}

func (m *mockOrgRepo) GetOrganization(ctx context.Context, orgID int) (*organization.Organization, error) {
	return m.org, nil
}

func TestAutoReplyService_FindMatchingTrigger(t *testing.T) {
	t.Parallel()
	ctx := context.Background()
	// 準備 mock data
	bot := &organization.Bot{ID: 1, OrganizationID: 100}
	org := &organization.Organization{ID: 100, Timezone: "Asia/Taipei"}
	bh := []organization.BusinessHour{}
	kw := &auto_reply.AutoReplyTriggerSetting{
		AutoReplyID: 1,
		Status:      auto_reply.AutoReplyStatusActive,
		Enable:      true,
		EventType:   auto_reply.AutoReplyEventTypeKeyword,
		Priority:    10,
		Keywords:    []string{"hello"},
	}
	gen := &auto_reply.AutoReplyTriggerSetting{
		AutoReplyID:         2,
		Status:              auto_reply.AutoReplyStatusActive,
		Enable:              true,
		EventType:           auto_reply.AutoReplyEventTypeTime,
		Priority:            5,
		TriggerScheduleType: ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		TriggerScheduleSettings: &auto_reply.WebhookTriggerScheduleSettings{
			Schedules: []auto_reply.WebhookTriggerSchedule{&auto_reply.DailySchedule{StartTime: "00:00", EndTime: "23:59"}},
		},
	}
	service := NewAutoReplyService(AutoReplyServiceParam{
		AutoReplyRepo:    &mockAutoReplyRepo{triggers: []*auto_reply.AutoReplyTriggerSetting{gen, kw}},
		BusinessHourRepo: &mockBusinessHourRepo{hours: bh},
		BotRepo:          &mockBotRepo{bot: bot},
		OrganizationRepo: &mockOrgRepo{org: org},
	})
	tests := []struct {
		name   string
		event  auto_reply.WebhookEvent
		expect *auto_reply.AutoReplyTriggerSetting
	}{
		{"keyword match", auto_reply.WebhookEvent{EventType: "message", MessageText: ptrString("hello"), Timestamp: time.Now()}, kw},
		{"general fallback", auto_reply.WebhookEvent{EventType: "message", MessageText: ptrString("notmatch"), Timestamp: time.Now()}, gen},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			result, err := service.FindMatchingTrigger(ctx, tc.event, bot.ID)
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if result == nil || result.AutoReplyID != tc.expect.AutoReplyID {
				t.Errorf("expect trigger id=%d, got %+v", tc.expect.AutoReplyID, result)
			}
		})
	}
}

// --- helper ---
func ptrString(s string) *string { return &s }
func ptrScheduleType(t auto_reply.WebhookTriggerScheduleType) *auto_reply.WebhookTriggerScheduleType {
	return &t
}
