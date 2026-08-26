// go-gin-postgresql-backend/src/models/db_language.go

package models

type Language struct {
	ID         int    `gorm:"column:language_id;primary_key"`
	Code       string `gorm:"column:language_code" json:"language_code" binding:"required"`
	Name       string `gorm:"column:language_name"`
	VectorName string `gorm:"column:vector_name"`
}
