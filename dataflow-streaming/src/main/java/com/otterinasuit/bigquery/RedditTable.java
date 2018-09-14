package com.otterinasuit.bigquery;

import com.google.api.services.bigquery.model.TableFieldSchema;
import com.google.api.services.bigquery.model.TableRow;
import com.google.api.services.bigquery.model.TableSchema;
import com.google.gson.Gson;
import com.otterinasuit.objects.RedditPost;
import org.apache.beam.sdk.transforms.DoFn;

import java.util.ArrayList;
import java.util.List;

public class RedditTable {

    /**
     * Convert RedditPost to BQ TableRow
     */
    public static class ConvertTableRow extends DoFn<RedditPost, TableRow> {

        @ProcessElement
        public void processElement(ProcessContext c) {
            try {
                TableRow row = c.element().getTableRow();

                c.output(row);
            } catch (Exception e) {
                // smol error help pls
                e.printStackTrace();
            }
        }
    }


    /**
     * Schema for reddit data
     * @return TableSchema
     */
    public static TableSchema getSchema(){
        List<TableFieldSchema> fields = new ArrayList<>();
        fields.add(new TableFieldSchema().setName("date_iso").setType("STRING"));
        fields.add(new TableFieldSchema().setName("author").setType("STRING"));
        fields.add(new TableFieldSchema().setName("num_comments").setType("INT"));
        fields.add(new TableFieldSchema().setName("subreddit").setType("STRING"));
        fields.add(new TableFieldSchema().setName("content").setType("STRING"));
        fields.add(new TableFieldSchema().setName("link").setType("STRING"));
        fields.add(new TableFieldSchema().setName("upvotes").setType("INT"));
        fields.add(new TableFieldSchema().setName("type").setType("STRING"));
        fields.add(new TableFieldSchema().setName("id").setType("STRING"));

        return new TableSchema().setFields(fields);
    }
}
