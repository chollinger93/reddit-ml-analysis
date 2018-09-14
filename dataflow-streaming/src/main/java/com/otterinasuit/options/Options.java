package com.otterinasuit.options;

import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptions;
import org.apache.beam.sdk.options.Validation;

public interface Options extends PipelineOptions {
    @Description("PubSub Topic to read from")
    String getTopic();
    void setTopic(String value);

    @Description("Output BQ table")
    @Validation.Required
    String getTable();
    void setTable(String value);

    @Description("Output BQ database")
    @Validation.Required
    String getDatabase();
    void setDatabase(String value);
}