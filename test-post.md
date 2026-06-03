Đây là một hệ sinh thái package/extension giúp mở rộng workflow agent, từ subagents, task management, memory, MCP integration cho tới guardrails và hiển thị tool output.

Một số package/extensions nên cài:
• Subagents: tạo và điều phối các sub-agent để chia nhỏ công việc phức tạp.
    https://www.npmjs.com/package/@tintinweb/pi-subagents
• Tasks: quản lý task/todo trong workflow Pi, giúp agent theo dõi tiến độ rõ ràng hơn.
    https://www.npmjs.com/package/@tintinweb/pi-tasks
• Memory Markdown: lưu và đọc memory dạng Markdown để giữ context giữa các lần chạy.
    https://www.npmjs.com/package/pi-memory-md
• MCP Adapter: kết nối Pi với MCP tools/server để mở rộng khả năng dùng tool.
    https://www.npmjs.com/package/pi-mcp-adapter
• Guardrails: thêm lớp kiểm soát/giới hạn hành vi để agent chạy an toàn và có nguyên tắc hơn.
    https://www.npmjs.com/package/@aliou/pi-guardrails
• Tool Display: cải thiện cách hiển thị tool call/tool output để dễ theo dõi agent đang làm gì.
    https://www.npmjs.com/package/pi-tool-display
• Augment: mở rộng khả năng của Pi bằng các hook/augmentation cho workflow agent.
    https://www.npmjs.com/package/pi-augment
• Multi-pass: hỗ trợ chạy nhiều lượt xử lý/đánh giá để cải thiện chất lượng output.
    https://github.com/hjanuschka/pi-multi-pass
• BTW: extension tiện ích cho workflow Pi, có thể dùng để bổ sung tương tác/nhắc ngữ cảnh trong lúc agent chạy.
    https://github.com/dbachelder/pi-btw
• Ask User Question: cho phép agent hỏi lại user khi thiếu thông tin thay vì đoán.
    https://github.com/ghoseb/pi-askuserquestion/
• VCC: package mở rộng workflow Pi, đáng xem nếu cần thêm cơ chế kiểm soát hoặc phối hợp agent.
    https://www.npmjs.com/package/@sting8k/pi-vcc
• Agent Modes: thêm các mode làm việc khác nhau cho agent, giúp chuyển cách vận hành theo từng loại task.
    https://www.npmjs.com/package/@danchamorro/pi-agent-modes
• Amp-like: mang trải nghiệm/workflow gần giống Amp vào Pi  (Nên nhớ Pi default là YOLO Mode, cài vào sẽ có thêm /persmission chỉnh, cũng như các phần liên quan đến amp như /handoff, /query-thread/session để tiếp tục với session/thread mới)
    https://www.npmjs.com/package/pi-amplike

========================================================================
Ngoài ra có thể bắt đầu nhanh với LazyPi:  (Nếu mới thử thì dùng LazyPi trước cho nhanh. Khi quen workflow rồi, có thể tự lắp các package cần thiết vào Pi theo nhu cầu)  . Còn không thì có thể cài ở trên là đủ rồi :smile: sau thiếu gì thì lắp vào tiếp :smile:
https://lazypi.org/
========================================================================
Nếu m.n có cursor thì có thể thử với package này để trải nghiệm Pi
https://pi.dev/packages/pi-cursor-sdk









=============================





Vài tips nhỏ sau một thời gian dùng Codex. Có mấy cái nhìn nhỏ nhưng ảnh hưởng khá nhiều tới độ bền context, khả năng điều khiển session, và cách scale work bằng agent/skills.

1. Bỏ /fast nếu muốn trụ lâu hơn. Fast mode tiện khi cần phản hồi nhanh, nhưng với task dài, nhiều tool call, hoặc cần reasoning kỹ thì nên /fast off để ưu tiên độ ổn định và chất lượng hơn tốc độ.

2. Dùng /side cho câu hỏi phụ. Nếu đang chạy main task mà muốn hỏi một câu liên quan nhưng không muốn làm nhiễu main context, dùng /side. Nó giống kiểu /btw trong Claude Code: mở một side conversation tách transcript khỏi parent thread, xong quay lại main task.

3. Nhấn ESC 2 lần để rewind/rollback khi thấy Codex đi sai ý. Đây là phanh khẩn cấp khá hữu dụng: thay vì tiếp tục giải thích trên một nhánh sai, rewind lại rồi steer lại prompt cho đúng.

4. Trigger skill bằng $ thường tiện hơn slash command. $skill-name tách biệt rõ với command điều khiển session, hợp khi muốn gọi workflow/capability cụ thể mà không lẫn với /model, /fast, /agent, /status, v.v.

5. Bật memories nếu muốn Codex nhớ context dài hạn. Cần bật cả feature và memory behavior trong ~/.codex/config.toml:

 toml
[features]
memories = true

[memories]
generate_memories = true
use_memories = trueLưu ý: memories hữu ích cho preference, repo convention, lesson learned; đừng kỳ vọng nó thay thế việc đọc source hiện tại.

6. Multi-agent của Codex chạy ở các session/thread khác nhau, ngang hàng với main agent. Dùng /agent để đảo giữa các agent threads. Có thể configure giới hạn như: toml
[agents]
max_depth = 1
max_threads = 12max_threads là số agent threads mở đồng thời, còn max_depth là độ sâu agent có thể spawn tiếp agent khác. Nói nôm na: có thể spam nhiều agents cùng lúc, hoặc cho agents có khả năng spawn tiếp theo depth. Kết hợp sub-agents + MCP + skills đặc thù là rất mạnh, miễn là task được chia rõ owner và output.

7. Codex CLI chạy được dưới dạng MCP Server. Nghĩa là có thể nhúng Codex vào workflow agent khác, ví dụ Agents SDK gọi Codex qua MCP để start/continue conversation. Đây là hướng hay nếu muốn build pipeline multi-agent deterministic hơn.

8. Hooks hiện tại đã ổn định hơn để dùng như lifecycle automation. Có thể cấu hình hooks trong hooks.json hoặc inline [hooks] trong config, và bật bằng features.hooks = true. Dùng tốt cho notify, guardrail, workflow check, hoặc log/evidence automation.

9. Bật js_repl nếu muốn batching tool calls, parsing outputs, data manipulation, transform JSON/CSV nhanh hơn trong session:

 toml
[features]
js_repl = trueNó hợp với các việc kiểu gom nhiều output, lọc dữ liệu, tính toán nhanh, hoặc chuẩn hóa payload trước khi đưa lại cho agent.

10. /goal thì... chờ đợi mòn mỏi và bào token :v. Nó hữu ích khi muốn Codex giữ một objective dài hơi trong thread, nhưng hiện vẫn nên dùng có kiểm soát. Official docs cũng ghi /goal là experimental và cần bật: toml
[features]
goals = trueClaude Code cũng vừa học lỏm kiểu này và release /goal tương tự Codex.

Bonus tips mình thấy đáng bật/thử thêm:

• Dùng /compact sau các phiên dài để giữ context gọn. Đừng đợi context gần nổ mới compact; compact sau mỗi milestone giúp agent giữ ý chính mà ít kéo rác cũ.
• Dùng /status thường xuyên để check model, permission, writable roots, token/context usage. Rất hữu ích khi thấy agent hành xử lạ do đang sai mode hoặc sai quyền.
• Dùng /diff trước khi bảo Codex sửa tiếp. Nó giúp mình nhìn đúng blast radius hiện tại, nhất là khi worktree đã có edits từ user hoặc từ agent khác.
• Dùng /mcp hoặc /mcp verbose để verify tools thật sự available. Plugin/config tồn tại không có nghĩa runtime hiện tại đã expose tool.
• Set config bền vững trong ~/.codex/config.toml, còn repo-specific behavior thì để .codex/config.toml trong trusted project. Tránh rely quá nhiều vào command-line override nếu đó là preference dùng lâu dài.
• Với task lớn, chia rõ main agent làm gì, subagent làm gì. Subagents mạnh nhất khi task độc lập, output rõ, và không đụng cùng file/phạm vi.

Ngoài ra có thể xem danh sách feature hiện có của Codex bằng:
`codex feature list`