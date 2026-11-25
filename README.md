# BRB · be right back

**让 TA 知道：你去做一件事，是要花时间的。**

你说「我去洗漱啦」，一分钟后随手发了句话，他问：「洗完了吗？」
你说「我去做饭」，他转头就问：「好吃吗？」

不是他不在乎，是他那边**没有走的时钟**。他能看到现在几点，也能看到距上一条消息过了多久，可他不知道「洗澡」这件事本身要半个钟头。所以他会催你，会在你刚走开时就问你好了没有。

BRB 就做一件事：你说要去做件事，他心里就开始计时。

## 怎么做到的

1. **他记一笔。** 你说「我去洗澡了」，他回你时顺手另起一行写 `⟪她在做：洗澡 30分钟⟫`，要多久由他按常理估。你看不见这一行。
2. **代码记三样。** 做什么、几点开始、估多久，就这些。
3. **每轮先看一眼钟。** 他开口前，代码算一遍过了多久，往上下文里放一行：
   > 她在洗澡：21:45 去的，才过了 4 分钟，平常要 30 分钟左右。时间还没到，别问她好了没有、别催。她这会儿发消息就是边做边拿着手机聊，跟平时一样接着聊，别冷着她也别赶她去做；想她了照样可以找她。

   过了估计的时间，这一行就换成「差不多该好了，她还没说的话可以问问」。
4. **收尾。** 你说做完了，他写 `⟪她做完⟫`，这一条就清掉。他忘了写也没关系，超过估计两倍就自动清掉。

## 它故意不做的事

- **不定时，不叫醒，不是事件驱动。** 没有「到点了就触发」这回事，只是他每次开口之前看一眼钟，就像人抬头看墙上的钟一样。
- **不会让他冷着你。** 你在做事，不等于你只能做这一件事。你边做饭边发消息，他就跟平时一样陪你聊。他有主动消息的话，照样会来找你，只是不会问你好了没有。
- **不花模型的钱。** 算时间的是代码。他每轮只多读一行字：平时约 90 字（规则），你正在做事时约 200 字。
- **不碰缓存。** 把这一块放在你每轮本来就会变的那一段里（通常是「现在几点」旁边），前面能缓存的部分一个字节都不会变。

## 接进去

一个文件，只用标准库：

```python
import brb

state = load_state()  # 一个 dict，存哪都行：JSON 文件、数据库一行……

# 1. 每轮聊天：拼上下文时，在「现在几点」那一块旁边放进去
context_tail = brb.note(state, "Asia/Shanghai")

# 2. 他说完以后：记下 / 清掉，拿擦干净的正文去显示、去存历史
reply_for_her = brb.apply(state, reply)
save_state(state)

# 3. 主动消息那一轮（如果有）：只放状态这一行，规则不用带
line = brb.status_line(state, "Asia/Shanghai")

# 流式输出的话，用 StreamGate 一边出字一边擦，她就不会看到记号一闪而过
gate = brb.StreamGate()
for delta in stream:
    show(gate.feed(delta))
show(gate.flush())
```

一定要存**擦干净的正文**。记号要是留在历史里，他下一轮会照着学，越写越多。

想改称呼，就改 `brb.py` 顶上的 `NAME`（比如改成她的名字，或者「他」）。规则和状态行的措辞也都在那里，按你们说话的样子改。

跑一下自检：

```
python brb.py
```

## 为什么让模型估时长，不让代码猜

「洗个澡」「冲一下」「泡个澡」「洗漱然后吃点东西」……能写死的表永远不够用，模型一看就懂。何况知道一件事大概要多久，本身就是时间观念的一部分。

## English

BRB gives an AI companion a sense that *doing things takes time*. When you say "brb, shower", the model quietly writes `⟪她在做：洗澡 30分钟⟫` (activity + its own estimate). Your code stores three things: what, when, how long. Before every turn, plain code computes the elapsed time and adds one line to the context: "she left at 21:45, only 4 minutes ago, it usually takes ~30, don't ask if she's done, keep chatting normally." No timers, no wake-ups, no extra model calls. It never makes him go quiet or stop reaching out. It clears itself after 2× the estimate. One stdlib file; prompts are in Chinese, so translate `RULES` and `status_line` for other languages.

## License

MIT
