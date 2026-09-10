output "bucket_name" {
  description = "Name of the data bucket"
  value       = aws_s3_bucket.data.id
}

output "bucket_arn" {
  value = aws_s3_bucket.data.arn
}
output "lambda_function_name" {
  value = aws_lambda_function.ingest.function_name
}