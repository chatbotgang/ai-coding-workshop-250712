package repository

import (
	"context"
	"sync"

	"github.com/chatbotgang/workshop/internal/domain/auto_reply"
)

// AutoReplyMemoryRepository 是 AutoReplyRepository 的記憶體實作

type AutoReplyMemoryRepository struct {
	mu     sync.RWMutex
	store  map[int]*auto_reply.AutoReply
	nextID int
}

func NewAutoReplyMemoryRepository() *AutoReplyMemoryRepository {
	return &AutoReplyMemoryRepository{
		store:  make(map[int]*auto_reply.AutoReply),
		nextID: 1,
	}
}

func (r *AutoReplyMemoryRepository) Create(ctx context.Context, ar *auto_reply.AutoReply) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	ar.ID = r.nextID
	r.nextID++
	r.store[ar.ID] = ar
	return nil
}

func (r *AutoReplyMemoryRepository) Update(ctx context.Context, ar *auto_reply.AutoReply) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.store[ar.ID]; !ok {
		return ErrNotFound
	}
	r.store[ar.ID] = ar
	return nil
}

func (r *AutoReplyMemoryRepository) Delete(ctx context.Context, id int) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.store[id]; !ok {
		return ErrNotFound
	}
	delete(r.store, id)
	return nil
}

func (r *AutoReplyMemoryRepository) GetByID(ctx context.Context, id int) (*auto_reply.AutoReply, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	ar, ok := r.store[id]
	if !ok {
		return nil, ErrNotFound
	}
	return ar, nil
}

func (r *AutoReplyMemoryRepository) ListByOrganization(ctx context.Context, orgID int) ([]*auto_reply.AutoReply, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	var result []*auto_reply.AutoReply
	for _, ar := range r.store {
		if ar.OrganizationID == orgID {
			result = append(result, ar)
		}
	}
	return result, nil
}

// ErrNotFound is returned when an entity is not found
var ErrNotFound = autoReplyRepoError{"auto_reply not found"}

type autoReplyRepoError struct {
	msg string
}

func (e autoReplyRepoError) Error() string {
	return e.msg
}
