FROM golang:1.26-alpine

RUN go install github.com/pressly/goose/v3/cmd/goose@latest

COPY migrate.sh /migrate.sh
RUN chmod +x /migrate.sh

ENTRYPOINT ["/migrate.sh"]
