## QRCodeGenerator

基于GitHub Actions，构建简单的静态二维码生成应用。

### 使用流程

1. 跳转到issues中的[QRCodeGenerator](https://github.com/yym6472/LearnGitHubActions/issues/3)
2. 将需要转换的内容作为输入，回复该issue
3. 稍等一会后，GitHub Actions后台会将生成的二维码图片作为回复提交到该issue，如下图：
   [![bx3QVf.png](https://s1.ax1x.com/2022/03/15/bx3QVf.png)](https://imgtu.com/i/bx3QVf)
   
### 实现

使用GitHub Actions作为后台，通过提交issue comment触发[配置的流程](../.github/workflows/gen-qrcode.yml)。流程触发后，后台将执行以下步骤：
- 将Repo代码下载到本地（使用[checkout](https://github.com/actions/checkout)）
- 安装python（使用[setup python](https://github.com/marketplace/actions/setup-python)）
- 通过pip安装依赖，这里需要安装的就是`qrcode`用于生成二维码，以及`pillow`用于生成图片
- 运行[python脚本](./gen_qr_code.py)根据内容生成二维码图片到本地，该脚本事先写好，接收内容和本地Repo路径作为参数，会将生成的二维码图片保存到`images`文件夹中，基于内容的md5进行命名，图片对应路径的markdown代码将作为脚本输出
- 生成图片后，使用git一系列命名上传、更新仓库（为了将生成的图片上传）
- 最后调用GitHub的RESTful API，将图片的markdown代码回复到对应的issue中（应该也能够使用其他的发送方式，比如邮件发送、微信通知（就需要调用微信API）等）

### workflow配置说明

配置的[yaml文件](../.github/workflows/gen-qrcode.yml)如下：
```yaml
name: Generate QR Code
on: 
  issue_comment:
    types: [created]
jobs: 
  generate_qr_code:
    if: ${{ github.event.issue.title == 'QRCodeGenerator' }}
    runs-on: ubuntu-latest
    steps:
      - run: echo "The comment is ${{ github.event.comment.body }}"
      - run: echo "The user is ${{ github.event.sender.login }}"
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.6'
          architecture: 'x64'
      - run: pip install pillow qrcode==7.3.1
      - name: Generate QR code image
        id: generate_qr_code_image
        run: echo "::set-output name=image_markdown_code::$(python ${{ github.workspace }}/QRCodeGenerator/gen_qr_code.py --message '${{ github.event.comment.body }}' --local_repo_path '${{ github.workspace }}')"
      - name: Commit and upload the generated image
        run: |
          git config --local user.email "yanyuanmeng1996@qq.com"
          git config --local user.name "yym6472"
          git remote set-url origin https://${{ github.actor }}:${{ secrets.GITHUB_TOKEN }}@github.com/${{ github.repository }}
          git add .
          git commit --allow-empty -m "Uploaded image"
          git push origin master
      - name: Submit image URI to issue (Through GitHub API)
        run: |
          echo "${{ steps.generate_qr_code_image.outputs.image_markdown_code }}"
          curl --request POST \
            --url https://api.github.com/repos/${{ github.repository }}/issues/${{ github.event.issue.number }}/comments \
            --header 'Authorization: token ${{ secrets.GITHUB_TOKEN }}' \
            --header 'Accept: application/vnd.github.v3+json' \
            --data '{"body": "The QR code for `${{ github.event.comment.body }}` is: \n${{ steps.generate_qr_code_image.outputs.image_markdown_code }}"}'
```

#### 第1行

```yaml
name: Generate QR Code
```

表示该流程的名字。

#### 第2~4行

```yaml
on: 
  issue_comment:
    types: [created]
```

表示在issue回复创建时触发，所有可以触发流程的事件以及说明可以在[这里](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows)找到。

#### 第5~6行

```yaml
jobs: 
  generate_qr_code:
```

一个流程是由多个job组成的，每个job独立运行在一台机器上，由若干steps构成，同时不同job之间可以配置依赖关系，以及可以有数据的传递。这里只有一个job，`generate_qr_code`是这个job的id。

#### 第7行

job下面的if，可以指定job运行的条件，不满足条件的job会被自动跳过。这里我设置的条件是触发（即有用户评论）的issue的标题需要是QRCodeGenerator，以此防止其他不相关的issue也触发这一流程。

另外这里的`${{ ... }}`是GitHub Actions的一种传递数据的语法形式，称为Contexts（上下文），极为有用，后面还要多次用到。详见[Contexts的官方文档](https://docs.github.com/en/actions/learn-github-actions/contexts)。
```yaml
    if: ${{ github.event.issue.title == 'QRCodeGenerator' }}
```

这里的`github.event`即[github context](https://docs.github.com/en/actions/learn-github-actions/contexts#github-context)中列出的一项，代表了对应的事件webhook。webhook可以理解成是GitHub一些事件（如代码提交、发布、PR、Issues等）发生后，GitHub后台会发送一个HTTP请求到指定的地址，已达到通知远端该事件发生的目的，可以理解成是一个远程回调。这个HTTP请求通常会包含相关事件的一些属性，比如Repo地址、发送PR/Issue的用户等等，以Json Object的形式发送过来。所以通过`github.event.xxx`就可以访问对应事件webhook对象的属性。

在[文档 events-that-trigger-workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows)中，提供了对应事件的webhook的形式。比如我们这里配置的`issue_comment`事件，其webhook对象包含的属性就在[这里](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#issue_comment)被列出。

进一步点进去[issue](https://docs.github.com/en/rest/reference/issues)或[comment](https://docs.github.com/en/rest/reference/issues#comments)，就可以分别找到issue对象和comment对象分别可访问到哪些属性。比如comment，就有内容（`body`）、用户（`user`）、创建时间（`created_at`）、（`updated_at`）等信息可以访问到。

#### 第8行

```yaml
    runs-on: ubuntu-latest
```
表示该job需要在哪类机器上运行。

#### 第9行

```yaml
    steps:
```
表示该job包含的steps，通过列表（`- ...`）的形式依次给出。

#### 第10~11行

```yaml
      - run: echo "The comment is ${{ github.event.comment.body }}"
      - run: echo "The user is ${{ github.event.sender.login }}"
```

`run: ...`即表示运行相应的命令，这里是将comment的信息和提交用户的ID输出日志。同样，对这两个信息的获取也使用了`${{ ... }}`的Contexts形式。在`issue_comment`事件webhook对象中，可通过`sender`属性获取提交comment的用户的Object。

#### 第12~16行

```yaml
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.6'
          architecture: 'x64'
```

`uses: ...`表示从外部引入已有的actions动作，通常是可以复用的一组动作的实现。GitHub提供了[Actions库](https://github.com/marketplace?type=actions)可以查找其他人编写的Actions，也可以[编写自己的Actions](https://docs.github.com/en/actions/creating-actions)。

这里的`actions/checkout`提供了[将相应的Repo从GitHub远端仓库中克隆到本地](https://github.com/actions/checkout)的功能；`actions/setup-python`提供了[安装python运行环境](https://github.com/marketplace/actions/setup-python)的功能，`@v2`均表示版本。`14~16`行是相应的参数，是action编写者暴露给用户的接口。

#### 第17行

```yaml
      - run: pip install pillow qrcode==7.3.1
```

使用pip安装`./gen_qr_code.py`需要的依赖。

#### 第18~20行

```yaml
      - name: Generate QR code image
        id: generate_qr_code_image
        run: echo "::set-output name=image_markdown_code::$(python ${{ github.workspace }}/QRCodeGenerator/gen_qr_code.py --message '${{ github.event.comment.body }}' --local_repo_path '${{ github.workspace }}')"
```

这一步命令比较复杂，其功能是运行python脚本，根据用户输入（即issue comment中的消息体）生成二维码图片，输出二维码图片的URL，同时需要记录URL传递给后面使用。

因为要把生成的二维码图片发送出去，那么必须要有静态资源托管网站，将生成的图片上传到上面生成资源URL。一种方法是将生成的图片上传到图床，但既然GitHub本身就可以托管静态资源，那么可以直接将图片上传到GitHub的仓库中获取URL。因此这里创建了`images`文件夹来专门储存图片。为了此前生成的图片不至于被覆盖，这里需要为图片生成不同的名字，所以使用了消息的md5值作为文件名，在生成对应的文件后，需要记住其URL，因为后面返回信息的时候还需要引用。

所以这里使用了GitHub Actions中[设置steps输出的语法](https://docs.github.com/en/actions/learn-github-actions/contexts#example-usage-of-the-steps-context)：`echo "::set-output name=<key>::<value>"`。在使用该语法后，后面就可以通过`steps.<step_id>.outputs.<key>`访问到相应的值了，这也是这一步需要使用`id: ...`设置step的id的原因。然后这里的`<key>`是可以自定义的，只需要在后面引用时保持相同即可，而`<value>`需要使用`$(...)`的语法，表示运行某个指令，并且将指令的输出作为值。在指令中，同样可以使用`${{ ... }}`的Contexts语法，它们会在命令运行开始就被GitHub Actions执行引擎替换成对应的值。

#### 第21~28行

```yaml
      - name: Commit and upload the generated image
        run: |
          git config --local user.email "yanyuanmeng1996@qq.com"
          git config --local user.name "yym6472"
          git remote set-url origin https://${{ github.actor }}:${{ secrets.GITHUB_TOKEN }}@github.com/${{ github.repository }}
          git add .
          git commit --allow-empty -m "Uploaded image"
          git push origin master
```

这一个step用于将生成的图片上传到仓库中，之前说了使用GitHub仓库来托管生成的图片。需要注意的是这里使用了`${{ secrets.GITHUB_TOKEN }}`作为认证的手段，它是在流程运行时由GitHub Actions引擎创建的一个秘密token，详见[关于安全和认证的文档](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)。

`run: |`的语法表示后面每行为一条命令（使用换行分隔），是[YAML表示多行文本的特殊语法](https://cloud.tencent.com/developer/article/1647114)。

#### 第29~36行
```yaml
      - name: Submit image URI to issue (Through GitHub API)
        run: |
          echo "${{ steps.generate_qr_code_image.outputs.image_markdown_code }}"
          curl --request POST \
            --url https://api.github.com/repos/${{ github.repository }}/issues/${{ github.event.issue.number }}/comments \
            --header 'Authorization: token ${{ secrets.GITHUB_TOKEN }}' \
            --header 'Accept: application/vnd.github.v3+json' \
            --data '{"body": "The QR code for `${{ github.event.comment.body }}` is: \n${{ steps.generate_qr_code_image.outputs.image_markdown_code }}"}'
```

这一个step使用GitHub API将上面得到的图片URL通过回复issue的形式上传、回复给用户。同样需要`${{ secrets.GITHUB_TOKEN }}`作为认证。另外这里使用了`${{ steps.generate_qr_code_image.outputs.image_markdown_code }}`来获取之前通过`echo "::set-output name=<key>::<value>"`传递的step输出。

关于创建issues回复的API，参见[这里](https://docs.github.com/en/rest/reference/issues#create-an-issue-comment)。

### 关于重复触发workflow的问题

一开始以为这样设计的方式，当后端通过RESTful API回复图片URL时，会再次触发GitHub Actions的流程（因为再次触发了`issue_comment`事件），后面发现通过RESTful API提交的回复用户为特殊的github-actions bot，因此并不会重复触发死循环。