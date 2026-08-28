package utils

import "go-gin-postgresql-backend/src/models"

func GetLanguageIDByCode(language *models.Language) (models.Language, error) {

	if err := models.DB.Raw("SELECT id AS language_id, code AS language_code, name AS language_name FROM languages WHERE code = ?", language.Code).Scan(&language).Error; err != nil {
		return models.Language{}, err
	}

	return *language, nil
}
