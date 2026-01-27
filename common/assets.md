# 从服务端获取播放数据
# 示例请求方法：

'''
curl --location --globoff 'http://192.168.41.135:1337/api/screen-scene-asserts?filters[screen][name][%24eq]=screen-d16&filters[scene][name][%24eq]=Huawei&sort=order%3Aasc&populate[assert][populate]=media' \
--header 'Authorization: Bearer 9cec8705d996b17ad80d3adba72e70182324c563170d2a3179072802cca31e6a8b54ad94596c3f1df88c201fed4e14e7d19a3d6b0926918deca7b8952bc655c9a827abc26a9c37dd495e5a93129791f186a0eb2ba47c44be9b6dcaaede088ef7027c6d4ecd365cf7e8374fe9f5832ca09ac3628a65d4949f050e3c0ef6911f7c'
'''

# 示例返回结果:

'''
{
    "data": [
        {
            "order": 1,
            "id": 30,
            "documentId": "cer1a7zqsw5xltzbtsw5eh7i",
            "createdAt": "2026-01-25T02:26:56.643Z",
            "updatedAt": "2026-01-26T03:37:23.404Z",
            "publishedAt": "2026-01-26T03:37:23.420Z",
            "config": null,
            "assert": {
                "id": 9,
                "documentId": "xjqtj5lrqaesnhvcingtkugy",
                "name": "B站宣传部片",
                "createdAt": "2026-01-26T01:59:00.096Z",
                "updatedAt": "2026-01-26T02:03:14.467Z",
                "publishedAt": "2026-01-26T02:03:14.480Z",
                "uri": "https://www.bilibili.com/video/BV1za4y117na/",
                "type": "webpage",
                "enable": null,
                "media": null
            }
        },
        {
            "order": 2,
            "id": 26,
            "documentId": "mlzh0jo0lr39mm7u6rtbtysv",
            "createdAt": "2026-01-26T01:39:43.320Z",
            "updatedAt": "2026-01-26T01:39:43.320Z",
            "publishedAt": "2026-01-26T01:39:43.329Z",
            "config": null,
            "assert": {
                "id": 12,
                "documentId": "rp3ke1356m5j3p4hhucr6liv",
                "name": "公司介绍-20250908",
                "createdAt": "2026-01-23T09:13:47.018Z",
                "updatedAt": "2026-01-26T02:21:03.270Z",
                "publishedAt": "2026-01-26T02:21:03.286Z",
                "uri": null,
                "type": "slide",
                "enable": null,
                "media": [
                    {
                        "id": 13,
                        "documentId": "xjviaduh4wp78ftz9lwjpk6p",
                        "name": "test-ppt-autoplay.pptx",
                        "alternativeText": null,
                        "caption": null,
                        "width": null,
                        "height": null,
                        "formats": null,
                        "hash": "test_ppt_autoplay_04dad80d6c",
                        "ext": ".pptx",
                        "mime": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        "size": 21363.82,
                        "url": "/uploads/test_ppt_autoplay_04dad80d6c.pptx",
                        "previewUrl": null,
                        "provider": "local",
                        "provider_metadata": null,
                        "createdAt": "2026-01-26T02:12:02.239Z",
                        "updatedAt": "2026-01-26T02:12:02.239Z",
                        "publishedAt": "2026-01-26T02:12:02.239Z"
                    }
                ]
            }
        },
        {
            "order": 3,
            "id": 31,
            "documentId": "temjaa6jpymk0zyxjzyriu10",
            "createdAt": "2026-01-25T02:31:25.200Z",
            "updatedAt": "2026-01-26T03:37:40.326Z",
            "publishedAt": "2026-01-26T03:37:40.335Z",
            "config": null,
            "assert": {
                "id": 11,
                "documentId": "nmucvtvq3dm8fkd9qqceovqt",
                "name": "人员介绍",
                "createdAt": "2026-01-23T09:50:19.176Z",
                "updatedAt": "2026-01-26T02:19:00.291Z",
                "publishedAt": "2026-01-26T02:19:00.303Z",
                "uri": null,
                "type": "video",
                "enable": null,
                "media": [
                    {
                        "id": 14,
                        "documentId": "w2fcy7lrqwxli3nycq5pwvsp",
                        "name": "xunjian.mp4",
                        "alternativeText": null,
                        "caption": null,
                        "width": null,
                        "height": null,
                        "formats": null,
                        "hash": "xunjian_ce6a4800aa",
                        "ext": ".mp4",
                        "mime": "video/mp4",
                        "size": 181317.98,
                        "url": "/uploads/xunjian_ce6a4800aa.mp4",
                        "previewUrl": null,
                        "provider": "local",
                        "provider_metadata": null,
                        "createdAt": "2026-01-26T02:16:17.367Z",
                        "updatedAt": "2026-01-26T02:16:17.367Z",
                        "publishedAt": "2026-01-26T02:16:17.367Z"
                    }
                ]
            }
        }
    ],
    "meta": {
        "pagination": {
            "page": 1,
            "pageSize": 25,
            "pageCount": 1,
            "total": 3
        }
    }
}
'''

# 参考以上的JSON数据结构，获取asserts的media的内容
# Bearer Token 从 config.py 中导入，get_cms_token()