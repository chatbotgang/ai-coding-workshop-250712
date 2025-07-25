package auto_reply

// Helper function to create string pointer
func stringPtr(s string) *string {
	return &s
}

// Helper function to convert string to pointer
func stringToScheduleType(s WebhookTriggerScheduleType) *WebhookTriggerScheduleType {
	return &s
}