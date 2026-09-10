resource "aws_cloudwatch_event_rule" "daily" {
  name                = "${var.project_name}-daily"
  description         = "Trigger ingestion once per day"
  schedule_expression = "cron(0 20 * * ? *)" # 05:00 JST
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "ingest" {
    rule      = aws_cloudwatch_event_rule.daily.name
  target_id = "ingest-lambda"
  arn       = aws_lambda_function.ingest.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily.arn
}