// go-gin-postgresql-backend/src/models/article_web.go

package models

import (
	"time"
)

type ArticleWeb struct {
	ID             string                 `json:"id" gorm:"type:uuid;primaryKey"`
	Title          string                 `json:"title" gorm:"column:title"`
	CreatedAt      time.Time              `json:"publishedDate" gorm:"column:created_at;type:timestamp without time zone"`
	Category       string                 `json:"category" gorm:"column:theme_name"`
	Tags           string                 `json:"tags" gorm:"column:tags;type:json"`
	Content        string                 `json:"content" gorm:"column:annotation"`
	LanguageCode   string                 `json:"language_code"`
	ImageSource    string                 `json:"image_source,omitempty"`
	SourceLink     string                 `json:"source_link,omitempty"`
	NeuralNetworks map[string]interface{} `gorm:"serializer:json" json:"neural_networks,omitempty"`
}

type ArticleWebQuery struct {
	LanguageCode string `form:"language_code" binding:"required"`
	ArticleID    string `form:"article_id,omitempty" binding:"omitempty"`
	Category     string `form:"category,omitempty" binding:"omitempty"`
	Query        string `form:"query,omitempty" binding:"omitempty"`
	Limit        int    `form:"limit,omitempty" binding:"omitempty"`
	Page         int    `form:"page,omitempty" binding:"omitempty"`
	Offset       int
}

type ArticleWebCount struct {
	Count int64 `json:"count"`
}
