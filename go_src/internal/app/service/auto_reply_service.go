package service

import (
	"context"

	"github.com/chatbotgang/workshop/internal/domain/auto_reply"
)

// AutoReplyServiceParam 用於依賴注入
// 可擴充 repository, logger 等

type AutoReplyServiceParam struct {
	AutoReplyRepository auto_reply.AutoReplyRepository
}

// AutoReplyService 提供自動回覆相關應用邏輯

type AutoReplyService struct {
	param AutoReplyServiceParam
	repo  auto_reply.AutoReplyRepository
}

func NewAutoReplyService(param AutoReplyServiceParam) *AutoReplyService {
	return &AutoReplyService{param: param, repo: param.AutoReplyRepository}
}

// ValidateTrigger 決定是否觸發自動回覆，包裝 domain 層邏輯
func (s *AutoReplyService) ValidateTrigger(ctx context.Context, input auto_reply.ValidateTriggerInput) auto_reply.TriggerResult {
	// 可加 log、trace、event 等應用層橫切
	return auto_reply.ValidateTrigger(input)
}
