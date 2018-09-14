package com.otterinasuit.objects;

import com.google.api.services.bigquery.model.TableRow;

import java.io.Serializable;

public class RedditPost implements Serializable {
    private int date_iso;

    public int getDateIso() { return this.date_iso; }

    public void setDateIso(int date_iso) { this.date_iso = date_iso; }

    private String author;

    public String getAuthor() { return this.author; }

    public void setAuthor(String author) { this.author = author; }

    private int num_comments;

    public int getNumComments() { return this.num_comments; }

    public void setNumComments(int num_comments) { this.num_comments = num_comments; }

    private String title;

    public String getTitle() { return this.title; }

    public void setTitle(String title) { this.title = title; }

    private String subreddit;

    public String getSubreddit() { return this.subreddit; }

    public void setSubreddit(String subreddit) { this.subreddit = subreddit; }

    private String content;

    public String getContent() { return this.content; }

    public void setContent(String content) { this.content = content; }

    private String link;

    public String getLink() { return this.link; }

    public void setLink(String link) { this.link = link; }

    private int upvotes;

    public int getUpvotes() { return this.upvotes; }

    public void setUpvotes(int upvotes) { this.upvotes = upvotes; }

    private String type;

    public String getType() { return this.type; }

    public void setType(String type) { this.type = type; }

    private String id;

    public String getId() { return this.id; }

    public void setId(String id) { this.id = id; }

    public TableRow getTableRow(){
        TableRow row = new TableRow()
                .set("date_iso", this.date_iso)
                .set("author", this.author)
                .set("num_comments", this.num_comments)
                .set("title", this.title)
                .set("subreddit", this.subreddit)
                .set("content", this.content)
                .set("link", this.link)
                .set("upvotes", this.upvotes)
                .set("type", this.type)
                .set("id", this.id);

        return row;
    }

    @Override
    public String toString() {
        return "RedditPost{" +
                "date_iso=" + date_iso +
                ", author='" + author + '\'' +
                ", num_comments=" + num_comments +
                ", title='" + title + '\'' +
                ", subreddit='" + subreddit + '\'' +
                ", content='" + content + '\'' +
                ", link='" + link + '\'' +
                ", upvotes=" + upvotes +
                ", type='" + type + '\'' +
                ", id='" + id + '\'' +
                '}';
    }
}
