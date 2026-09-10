resource "aws_glue_catalog_database" "main" {
  name        = replace(var.project_name, "-", "_")
  description = "YouTube chart data"
}

resource "aws_glue_catalog_table" "videos" {
  name          = "videos"
  database_name = aws_glue_catalog_database.main.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification            = "parquet"
    "parquet.compression"     = "SNAPPY"
    EXTERNAL                  = "TRUE"
    "projection.enabled"      = "true"
    "projection.dt.type"      = "date"
    "projection.dt.range"     = "2026-08-01,NOW"
    "projection.dt.format"    = "yyyy-MM-dd"
    "projection.dt.interval"  = "1"
    "projection.dt.interval.unit" = "DAYS"
    "projection.region.type"  = "enum"
    "projection.region.values" = "JP"
    "storage.location.template" = "s3://${aws_s3_bucket.data.id}/curated/dt=$${dt}/region=$${region}"
  }

  partition_keys {
    name = "dt"
    type = "string"
  }

  partition_keys {
    name = "region"
    type = "string"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data.id}/curated/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "video_id"
      type = "string"
    }
    columns {
      name = "title"
      type = "string"
    }
    columns {
      name = "channel_id"
      type = "string"
    }
    columns {
      name = "channel_title"
      type = "string"
    }
    columns {
      name = "category_id"
      type = "string"
    }
    columns {
      name = "published_at"
      type = "timestamp"
    }
    columns {
      name = "tag_count"
      type = "int"
    }
    columns {
      name = "duration_seconds"
      type = "int"
    }
    columns {
      name = "view_count"
      type = "bigint"
    }
    columns {
      name = "like_count"
      type = "bigint"
    }
    columns {
      name = "comment_count"
      type = "bigint"
    }
    columns {
      name = "region_code"
      type = "string"
    }
  }
}