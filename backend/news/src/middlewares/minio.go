package middlewares

import (
	"bytes"
	"context"
	"os"

	minio "github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
)

type MinioClient struct {
	*minio.Client
}

func NewMinioClient() (*MinioClient, error) {
	host := os.Getenv("MINIO_HOST") + ":9000"
	accessKey := os.Getenv("MINIO_USER")
	secretKey := os.Getenv("MINIO_PASSWORD")

	client, err := minio.New(host, &minio.Options{
		Creds:  credentials.NewStaticV4(accessKey, secretKey, ""),
		Secure: false,
	})
	if err != nil {
		return nil, err
	}

	return &MinioClient{client}, nil
}

func (m *MinioClient) EnsureBucketExists(bucketName string) error {
	exists, err := m.BucketExists(context.Background(), bucketName)
	if err != nil {
		return err
	}
	if !exists {
		err = m.MakeBucket(context.Background(), bucketName, minio.MakeBucketOptions{ObjectLocking: false})
		if err != nil {
			if minio.ToErrorResponse(err).Code != "BucketAlreadyOwnedByYou" {
				return err
			}
		}
		policy := `{
			"Version": "2012-10-17",
			"Statement": [
				{
					"Effect": "Allow",
					"Principal": {"AWS": "*"},
					"Action": ["s3:GetBucketLocation", "s3:ListBucket"],
					"Resource": "arn:aws:s3:::` + bucketName + `"
				},
				{
					"Effect": "Allow",
					"Principal": {"AWS": "*"},
					"Action": "s3:GetObject",
					"Resource": "arn:aws:s3:::` + bucketName + `/*"
				}
			]
		}`
		err = m.SetBucketPolicy(context.Background(), bucketName, policy)
		if err != nil {
			return err
		}
	}
	return nil
}

func (m *MinioClient) UploadFromFile(bucketName, objectName, filePath string) error {
	err := m.EnsureBucketExists(bucketName)
	if err != nil {
		return err
	}
	_, err = m.FPutObject(context.Background(), bucketName, objectName, filePath, minio.PutObjectOptions{})
	return err
}

func (m *MinioClient) UploadFromBytes(bucketName, objectName string, data []byte) error {
	err := m.EnsureBucketExists(bucketName)
	if err != nil {
		return err
	}
	dataStream := bytes.NewReader(data)
	_, err = m.PutObject(context.Background(), bucketName, objectName, dataStream, int64(len(data)), minio.PutObjectOptions{})
	return err
}
