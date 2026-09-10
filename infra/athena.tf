resource "aws_athena_workgroup" "main" {
  name = var.project_name
  tags = local.common_tags

  configuration {
    enforce_workgroup_configuration = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.data.id}/athena-results/"
    }
  }
}