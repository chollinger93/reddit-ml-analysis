package com.otterinasuit;

import com.google.api.services.bigquery.model.TableRow;
import com.google.gson.Gson;
import com.otterinasuit.bigquery.RedditTable;
import com.otterinasuit.objects.RedditPost;
import com.otterinasuit.options.Options;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.PCollection;


public class DataFlowStreaming {

    /**
     * Parses a post from JSON to a RedditPost object
     */
    private static class ParsePostFn extends DoFn<String, RedditPost> {

        @ProcessElement
        public void processElement(ProcessContext c) {
            try {
                Gson g = new Gson();
                String json = c.element();
                RedditPost post = g.fromJson(json, RedditPost.class);
                c.output(post);
            } catch (Exception e) {
                // smol error help pls
                e.printStackTrace();
            }
        }
    }

    /**
     * Main pipeline entry point
     *
     * @param options Command line arguments
     */
    private static void run(Options options) {
        // https://github.com/apache/beam/blob/master/examples/java/src/main/java/org/apache/beam/examples/complete/game/LeaderBoard.java
        Pipeline p = Pipeline.create(options);

        // Build pipeline
        PCollection<TableRow> rows = p.apply(PubsubIO.readStrings()
                .fromTopic(options.getTopic()))
                .apply("Parse post from JSON", ParDo.of(new ParsePostFn()))
                .apply("Parse post to TableRow", ParDo.of(new RedditTable.ConvertTableRow()));


        rows.apply(BigQueryIO.writeTableRows()
                .to(options.getDatabase() + "." + options.getTable())
                .withSchema(RedditTable.getSchema())
                .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_APPEND));

        p.run().waitUntilFinish();
    }

    public static void main(String[] args) {
        Options options =
                PipelineOptionsFactory.fromArgs(args).withValidation().as(Options.class);

        run(options);
    }
}
