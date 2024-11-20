# Fine Tuning LLM

I have used Wordpress in the system to create different blogs and documentations. I have planned to attach a LLM to the django application that will answer questions regarding the blogs and documentations. 

**This folder contains the code to train and finetune the model since the main python application will run on web server and may not have GPU.**

Currently the training will be done on a separate machine and the fine-tuned model will be used by the django application.

## 1.0 Fine-tuning and deploying the LLM

1. Choose an open-source LLM to use via HuggingFace. It can either be Llama 2 or Gemma-2-2b (Preferred as the model is smaller).

2. Fetch the list of all posts available in the wordpress CMS. Use the Rest API to fetch the data.

3. Fetch the content, tag, title, excerpt, and metadata (id, publish date, author, link, and categories).

4. Preprocess all the posts to create a dataset.

5. Fine-tune the model with the dataset. Preferrably quantize the model to use 4-bit params.

6. Save the fine-tuned model and publish it to the Django application so that the application uses the latest model.

7. Redeploy the Django application to recreate the model using the newer version.


## 2.0 Model Information

I have currently chosen the following LLM models for the task.

### 2.1 Llama2-7b

- **HuggingFace:** NousResearch/Llama-2-7b-chat-hf

- **Estimated file size:** ~ 13 GB

- **Model Parameters:** 7B

- **Open-Source:** Yes

- **Model Type:** Causal LM

- **Documentation:** [https://huggingface.co/NousResearch/Llama-2-7b-chat-hf](https://huggingface.co/NousResearch/Llama-2-7b-chat-hf)


### 2.1 Gemma 2-2b (Preferred)

- **HuggingFace:** google/gemma-2-2b

- **Estimated file size:** ~ 9 GB

- **Model Parameters:** 2B

- **Open-Source:** Yes

- **Model Type:** Causal LM

- **Documentation:** [https://huggingface.co/google/gemma-2-2b](https://huggingface.co/google/gemma-2-2b)


## 3.0 Dataset Information

The dataset is a collection of all posts published in the Portfolio application. The posts are stored in the Wordpress CMS. It will be retrieved using Rest API. 

### 3.1 Post Category

A post belongs to one root category and one or more sub-categories. A **root** category is the category that does not have a parent. Categories with parents are **sub-categories.** This system creates a navigation context for the posts.

**Current root categories:**

- Blogs

- Documentation

**Endpoints:**

- List categories: [https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/categories](https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/categories)

**Sample request:**
```
import requests

url = "https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/categories"

payload={}
headers = {
  'Authorization': 'Basic token'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
```

**Sample response:**

```
[
    {
        "id": 37,
        "count": 3,
        "description": "Documentation related to different components of the application layer",
        "link": "https://wpbackend.vip3rtech6069.com/category/documentation/docs-application-layer/",
        "name": "Application Layer",
        "slug": "docs-application-layer",
        "taxonomy": "category",
        "parent": 2,
        "meta": [],
        "_links": {
            "self": [
                {
                    "href": "https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/categories/37"
                }
            ]
        }
    },
    {
        "id": 21,
        "count": 4,
        "description": "Posts related to different blogs",
        "link": "https://wpbackend.vip3rtech6069.com/category/blogs/",
        "name": "Blogs",
        "slug": "blogs",
        "taxonomy": "category",
        "parent": 0,
        "meta": [],
        "_links": {
            "self": [
                {
                    "href": "https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/categories/21"
                }
            ]
        }
    },
    {
        "id": 2,
        "count": 5,
        "description": "Post related to documentation",
        "link": "https://wpbackend.vip3rtech6069.com/category/documentation/",
        "name": "Documentation",
        "slug": "documentation",
        "taxonomy": "category",
        "parent": 0,
        "meta": [],
        "_links": {
            "self": [
                {
                    "href": "https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/categories/2"
                }
            ]
        }
    }
]
```

- Category Detail: [https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/categories/{category_id}](https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/categories/2)

**Sample request:**

```
import requests
category_id=2
url = f"https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/categories/{category_id}"

payload={}
headers = {
  'Authorization': 'Basic token'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)

```

**Sample response:**

```
{
    "id": 2,
    "count": 5,
    "description": "Post related to documentation",
    "link": "https://wpbackend.vip3rtech6069.com/category/documentation/",
    "name": "Documentation",
    "slug": "documentation",
    "taxonomy": "category",
    "parent": 0,
    "meta": [],
    "_links": {
        "self": [
            {
                "href": "https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/categories/2"
            }
        ]
    }
}
```
### 3.2 Post

A post is a wordpress post displayed on the website. The following parameters of a post will be used for the dataset:

- **ID:** The unique GUID of the post (String).

- **Title:** The title of the post (String - Plain text)

- **Excerpt:** The excerpt of the post (String - html)

- **Publish date:** The date when the post was published (String - UTC formatted string)

- **Author:** The ID of the author of the post (Int - Foreign key)

- **Content:** The content of the post (String - html)

- **Categories:** ID of categories that the post belongs to (List[int] - Foreign key)

- **Tags:** ID of tags that the post has (List[int] - Foreign key)


**Endpoints:**

- Post Detail: [https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/posts/{post_id}](https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/posts/2648)

**Sample request:**

```
import requests

post_id = 2648
url = f"https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/posts/{post_id}"

payload={}
headers = {
  'Authorization': 'Basic token'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
```

**Sample response:**

```
{
    "id": 2648,
    "date": "2024-11-17T16:15:52",
    "date_gmt": "2024-11-17T16:15:52",
    "guid": {
        "rendered": "https://wpbackend.vip3rtech6069.com/?p=2648"
    },
    "modified": "2024-11-17T16:19:35",
    "modified_gmt": "2024-11-17T16:19:35",
    "slug": "traversing-a-spiral-matrix",
    "status": "publish",
    "type": "post",
    "link": "https://wpbackend.vip3rtech6069.com/2024/11/17/traversing-a-spiral-matrix/",
    "title": {
        "rendered": "Traversing a spiral matrix"
    },
    "content": {
        "rendered": "<h1>Hello World</h1>",
        "protected": false
    },
    "excerpt": {
        "rendered": "<p>This is an excerpt</p>\n",
        "protected": false
    },
    "author": 3,
    "featured_media": 45,
    "comment_status": "open",
    "ping_status": "open",
    "sticky": false,
    "template": "elementor_canvas",
    "format": "standard",
    "meta": {
        "footnotes": ""
    },
    "categories": [
        15,
        21,
        3
    ],
    "tags": [
        67,
        71,
        14,
        68,
        72,
        70
    ],
    "class_list": [
        "post-2648",
        "post",
        "type-post",
        "status-publish",
        "format-standard",
        "has-post-thumbnail",
        "hentry",
        "category-data-structure-arrays",
        "category-blogs",
        "category-data-structure",
        "tag-array",
        "tag-competitive-programming",
        "tag-data-structure",
        "tag-matrix",
        "tag-spiral",
        "tag-traversal"
    ],
    "_links": {
        "self": [
            {
                "href": "https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/posts/2648"
            }
        ]
    }
}
```

### 3.3 Author

This endpoint will be used to get the author details for a post.

**Endpoints:**

- Author Details: [https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/users/{author_id}](https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/users/1)

**Sample request:**

```
import requests

author_id = 1
url = f"https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/users/{author_id}"

payload={}
headers = {
  'Authorization': 'Basic token'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)

```

**Sample response:**

```
{
    "id": 1,
    "name": "john doe",
    "url": "https://wpbackend.vip3rtech6069.com",
    "description": "",
    "link": "https://wpbackend.vip3rtech6069.com/author/john/",
    "slug": "john",
    "avatar_urls": {
        "24": "https://secure.gravatar.com/avatar/3b72b2972fbca0251acf6677a0f01a78?s=24&r=g",
    },
    "meta": [],
    "_links": {
        "self": [
            {
                "href": "https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/users/1"
            }
        ],
        "collection": [
            {
                "href": "https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/users"
            }
        ]
    }
}
```

### 3.4 Tag

This endpoint will be used to fetch information related to different tags attached to the post.

**Endpoints:**

- Tag Detail: [https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/tags/{tag_id}](https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/tags/67)

**Sample request:**

```
import requests

tag_id = 67
url = f"https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/tags/{tag_id}"

payload={}
headers = {
  'Authorization': 'Basic token'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)

```

**Sample response:**

```
{
    "id": 67,
    "count": 1,
    "description": "",
    "link": "https://wpbackend.vip3rtech6069.com/tag/array/",
    "name": "array",
    "slug": "array",
    "taxonomy": "post_tag",
    "meta": [],
    "_links": {
        "self": [
            {
                "href": "https://wpbackend.vip3rtech6069.com/wp-json/wp/v2/tags/67"
            }
        ]
    }
}
```

## 4.0 Data Schema for the LLM

The main dataset for the llm is a list of posts published in the system. Each post is an object that contains some specific information. **Section 3.0 contains the data schema for the posts currently stored in Wordpress. However, we need to preprocess and format the data to be used efficiently for the LLM. This section contains the data schema for training the LLM Model.**


### 4.1 Post

A post is an object that mainly contains two type of data - Post content and metadata.

**Quering the LLM**

- When querying the LLM we will provide only the **post content** as the context. The LLM will respond to the query based on the context. However, it is not neccessary or recommended to feed the whole post content as that will waste a lot of tokens. Moreover, we may concatenate the preprocessed content of multiple posts if required. So, we need to preprocess the post content before storing it so that it only contains important information like text and url links, and image links. We will try to strip out other unneccessary information like html tags, scripts, etc. **We will use beautifulsoup to preprocess the data.**

- We will use the **metadata** to fetch the relevant post contents that needs to be fed to the LLM. For example, let us consider a scenario where a user asks questions related to a specific post. In that case, when a user starts the conversation, metadata like Post ID will be used to fetch the correct post from wordpress. We will use the relevant section of this post as the context.


**Training the LLM**

RAG is a powerful technique but it requires us to send related documents from database as context which wastes a lot of token. Fine-tuning the model with the post data will ensure that even if we pass small context, the model will be able to provide response based on the learnt context.

We will fine-tune the model based on the post data. All data will be stored in Weaviate database and when the training starts we will fetch all posts from the weaviate database. Each post will contain the following schema:

1. **postId:** The unique GUID of the post. This will be indexed and searchable to retrieve individual post content if required.

2. **postTitle:** Title of the post as text. This will be vectorized and used in filtering and semantic search.

3. **postExcerpt:** Excerpt of the post as text. This will be vectorized and used in semantic search.

4. **postContent:** Content of the post as text. This will be vectorized and used for semantic search.

5. **postDate:** The publish datetime of the post as datetime. This will indexed and searchable to retrieve posts within a specific date range. The post date will also be concatenated with the post content to be included in semantic search.

6. **postAuthor:** Name of the author of the post as text. This will be indexed and searchable to retrieve posts by specific author. The author name will also be concatenated with the post content to be included in semantic search.

7. **postCategories:** Comma-separated name of categories related to the post as text. This will be indexed and used in filtering the data. The categories will also be concatenated with the post content to be included in semantic search.

8. **postTags:** Comma-separated name of tags related to the post as text. These will also be concatenated with the post content to be included in semantic search.

9. **postUrl:** Url of the post as text. This will also be concatenated with the post content to be included in semantic search.

