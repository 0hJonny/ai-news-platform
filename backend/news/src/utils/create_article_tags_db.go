package utils

import "gorm.io/gorm"

func insertArticleWithTags(articleID string, tags []string, db *gorm.DB) error {
	for _, tag := range tags {
		var existingTag struct {
			TagID   int
			TagName string
		}
		query := `SELECT tag_id FROM tags WHERE tag_name = ?`
		err := db.Raw(query, tag).Scan(&existingTag).Error
		if err != nil && err != gorm.ErrRecordNotFound {
			return err
		}
		if existingTag.TagID == 0 {
			query := `INSERT INTO tags (tag_name) VALUES (?) RETURNING tag_id`
			err := db.Raw(query, tag).Scan(&existingTag).Error
			if err != nil {
				return err
			}
		}
		query = `
			INSERT INTO article_tags (article_id, tag_id) 
			SELECT ?, ? 
			WHERE NOT EXISTS (SELECT 1 FROM article_tags WHERE article_id = ? AND tag_id = ?)
		`
		err = db.Exec(query, articleID, existingTag.TagID, articleID, existingTag.TagID).Error
		if err != nil {
			return err
		}
	}
	return nil
}
