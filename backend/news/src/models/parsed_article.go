// go-gin-postgresql-backend/src/models/parsed_article.go

package models

import "time"

type ParsedArticle struct {
	ID       string    `json:"id" gorm:"type:uuid;primaryKey"`
	Title    string    `json:"title" binding:"required" gorm:"column:title"`
	Author   string    `json:"author" binding:"required" gorm:"column:author"`
	PostHref string    `json:"post_href" binding:"required"`
	Body     string    `json:"body" binding:"required" gorm:"column:body"`
	Image    string    `json:"image" binding:"required"`
	Date     time.Time `json:"date" binding:"required" gorm:"column:post_date"`
	Language Language  `gorm:"foreignKey:language_id"`
}

type CheckForExistingParsedArticle struct {
	PostHref string `json:"article_href" binding:"required"`
	Exists   bool   `json:"exists" gorm:"column:exists"`
}
