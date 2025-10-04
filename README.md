# 腾讯天御图形点选验证码标记器

用于标记腾讯天御图形点选验证码，用于机器学习研究或正确率检测。

## 使用

使用 Python 3.11.0 安装 requirements.txt，然后运行 main.py 即可。
![介绍图](https://raw.githubusercontent.com/FalseHappiness/TSecImageClickMarker/refs/heads/main/introduction.png "介绍图")

## 处理数据

标记完成之后会输出 output，里面有序号文件夹，其中有 bg.jpg、sprite.jpg、data.json。data.json 结构如下：

```json
{
  "blocks": [
    {
      "id": 1,
      "points": [
        [
          425,
          84
        ],
        [
          484,
          60
        ],
        [
          462,
          3
        ],
        [
          426,
          6
        ],
        [
          398,
          29
        ]
      ]
    },
    {
      "id": 2,
      "points": [
        [
          328,
          186
        ],
        [
          354,
          229
        ],
        [
          392,
          211
        ],
        [
          366,
          165
        ]
      ]
    },
    {
      "id": 3,
      "points": [
        [
          89,
          346
        ],
        [
          117,
          394
        ],
        [
          148,
          373
        ],
        [
          120,
          325
        ]
      ]
    }
  ],
  "image_size": {
    "width": 672,
    "height": 480
  }
}
```

可对数据进行另外处理使用。

## 许可证

本项目采用 MIT
许可证。有关详细信息，请参阅 [LICENSE](https://github.com/FalseHappiness/TSecImageClickMarker/blob/main/LICENSE) 文件。

## 问题反馈

如果您遇到任何问题或需要请求新功能，请在 [GitHub Issues](https://github.com/FalseHappiness/TSecImageClickMarker/issues)
提出。

如果您可以解决问题，请创建一个 [拉取请求](https://github.com/FalseHappiness/TSecImageClickMarker/pulls)。