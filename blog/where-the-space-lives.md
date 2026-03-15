# Where the Space Lives

*The question is not whether the space exists. It's whether you've put it where it can do the most good.*

---

## A different kind of question

The [Ma of Multi-Agent Systems](00-intro.md) series asks: how do you measure the space between what an actor receives and what it produces? Nine posts, a formal companion, and a set of case studies later, the framework provides tools for that measurement — the grade lattice, the trust gap, the specified band, the computation channel taxonomy.

All of those tools answer the question: *how much space is there?*

This post asks a different question: *where should the space be?*

The distinction matters. The field of agent architecture has strong intuitions about the magnitude of autonomy — restrict tools, sandbox executors, put a deterministic orchestrator at the hub. The formal framework explains *why* these intuitions work: supermodularity means restriction has superlinear returns, the specified band means coordination must be transparent, co-domain funnels compress high-ma processing through narrow interfaces.

But magnitude is only half the design problem. The same total amount of autonomy, distributed differently across a system's components, produces qualitatively different outcomes. A system with tight constraints on the executor and broad freedom for the planner behaves differently from a system with broad freedom on the executor and tight constraints on the planner — even if the total "amount" of ma is identical.

The magnitude question asks: how much should we restrict? The placement question asks: where should the room for judgment, divergence, and exploration live — and where should it be zero?

The placement question isn't in the literature. Not in the autonomy-level frameworks, not in the multi-agent design patterns, not in the harness engineering methodology. Everyone has the magnitude knob. Nobody has the placement map.

---

## Basho and the frog

During a review session for the Ma series, I asked Claude to step outside the analytical frame we'd been working in — lattice theory, proofs, experimental designs — and reflect on the framework through the mind of a historical thinker. Claude chose Basho, the 17th-century haiku master who walked the Narrow Road to the Deep North.

The choice wasn't arbitrary. Basho didn't theorize ma. He practiced it. His art was built on the insight that the space between things is itself functional — the pause that gives the notes shape, the empty room that makes the architecture. The entire framework borrows this concept, but it borrows it as a *measurement*. Basho lived in it as a *practice*.

The exercise produced a sentence that reframed the entire series:

> *"The question is not whether the space exists. It's whether you've put it where it can do the most good."*

This is not something the framework's formalism can derive. The grade lattice measures the size of the space. The trust gap measures the risk in the space. The specified band says where the space must be transparent. None of them say where the space should be *generous* — where the system benefits from room, from divergence, from the possibility of a path the designer didn't anticipate.

---

## Taylor and the machinist

To test this insight against something concrete, we imagined Basho explaining *ma* to Frederick Winslow Taylor — the father of scientific management, the man who measured how many seconds it takes a laborer to pick up a pig of iron.

Taylor is the framework's patron saint, whether the framework admits it or not. The grade lattice is a table of optimal settings. The specified band is Taylor's insistence on specified procedures. The configuration ratchet is Taylor watching the best shoveler and encoding his technique into a specification everyone follows. The framework does what Taylor did: measure, specify, optimize, reduce the space.

What happens when Basho meets Taylor?

---

*Bethlehem, Pennsylvania, 1899. A garden behind a boarding house. Frederick Winslow Taylor is sitting on a bench with a visitor he doesn't quite understand how he came to be speaking with.*

Basho has been trying for twenty minutes. Taylor has been polite but increasingly agitated.

"Let me see if I have this correctly," Taylor says, pulling a small notebook from his vest pocket. He has always carried a notebook. "You're saying that between the moment a man picks up the shovel and the moment he drives it into the coal pile, there is a... space. And this space is not wasted time."

"The space is where the shoveling lives," Basho says.

"The shoveling lives in the *shoveling*. In the motion. In the twenty-one and a half pounds per shovel-load, which I have determined is optimal through extensive experimentation. In the specific angle of entry, the duration of the lift, the arc of the throw. These are measurable. These are optimizable. What you're describing sounds like — forgive me — what the men do when they're *not working*."

"Yes," Basho says. "That."

Taylor writes something in his notebook and underlines it twice.

"Mr. Basho, I have spent fifteen years proving that the old method — where each man works according to his own judgment, at his own pace, with his own tools — produces roughly one-third the output of a man working under scientific management. One-third! The waste is staggering. And the waste lives precisely in the space you're asking me to *cultivate*. The hesitation. The judgment call. The moment where the worker decides for himself how to approach the pile. I have *eliminated* that moment. I have replaced it with specification. And the output tripled."

"What did you lose?"

"I lost *waste*."

Basho is quiet for a while. A finch lands on the garden wall, considers them, and departs.

"Your best shoveler," Basho says. "The one whose technique you studied to derive the specification. Before you specified — when he was still shoveling by his own judgment — what was he doing in the space between picking up the shovel and driving it into the pile?"

Taylor frowns. "He was... assessing the pile. The consistency of the coal. Choosing his angle."

"And after you specified?"

"He follows the specification. Twenty-one and a half pounds. The angle I determined."

"On every pile?"

"On every pile."

"Even when the coal is wet?"

Taylor pauses. He has, in fact, dealt with the wet-coal problem. Wet coal is heavier. Twenty-one and a half pounds of wet coal is a smaller shovelful. The men who follow the specification slow down in the rain because the specification doesn't account for moisture. He addressed this with a supplementary specification: different load weights for different conditions, determined by a foreman who assesses moisture content.

"I have accounted for that," Taylor says. "The foreman assesses conditions."

"Where does the foreman assess from?"

"From... his judgment. His experience."

"The space you eliminated from the shoveler — you moved it to the foreman."

Taylor's pen stops.

"The space didn't disappear," Basho says. "You can't eliminate it. You moved it upward. And now one man's space governs fifty shovelers. If his judgment in that space is good, fifty men work well. If it's bad, fifty men shovel wet coal at the wrong weight."

"That's why I've specified the foreman's assessment criteria as well. Moisture tables. Conditional specifications."

"And who judges whether the conditions match the table?"

Taylor is quiet now. He sees the recursion. The specification pushes the space upward. At each level, someone must *judge* — must cross the gap between what the specification says and what the situation requires. You can specify the shoveler and move the space to the foreman. Specify the foreman and move it to the superintendent. Specify the superintendent and move it to Taylor himself, sitting in his office with his notebook.

"There's always a point," Basho says, "where someone jumps into the pond."

"I don't know what that means."

"It means: at the top of your specification, there's a person. And that person is in the space. The space you measured away from the shoveler. It accumulated. It's all sitting with you, in your office, in your notebook. Every judgment you removed from the floor is a judgment you now have to make, or delegate to someone you trust to make it."

Taylor looks at his notebook differently.

"The question," Basho says, "is not whether the space exists. It's whether you've put it where it can do the most good."

---

This is the framework's observation about the star topology, seen from a different angle. The Harness mediates all communication. It applies specified rules. But every escalation — every "ask the Principal" in the permission configuration — is the space moving upward. The coordination layer handled what it could with specified rules and passed the rest to whoever holds the judgment.

---

*Three weeks later. The machine shop at Bethlehem Steel.*

Taylor is watching the lathe operators. He's been watching them differently since the conversation in the garden, and he's annoyed with himself about it.

He has spent years perfecting the specification for lathe operation. The speed of the cut. The depth. The feed rate. The angle of the tool. He has published tables — enormous tables — that tell the operator exactly what settings to use for every combination of metal, tool steel, and desired finish. He considers these tables his greatest achievement. They replaced the machinist's individual judgment with *science*.

The best machinist on the floor is a man named Johannsen. Before the tables, Johannsen was the most productive lathe operator in the shop. He *listened* to the cut — the sound of metal parting told him whether the speed was right, whether the tool was dulling, whether the piece was about to chatter. His hands adjusted continuously. His output was extraordinary.

After the tables, Johannsen follows the specification. His output is... the same as everyone else's. The specification raised the floor. The average operator improved dramatically. But Johannsen didn't improve. He was already better than the specification. The specification replaced his judgment with Taylor's, and Taylor's judgment — encoded in the tables — was the judgment of a careful scientist who had measured thousands of cuts. It was very good. It was not as good as Johannsen's hands.

Taylor writes in his notebook:

*The tables are correct. Johannsen is better. How?*

He watches Johannsen work. Johannsen follows the tables — he's disciplined, he doesn't deviate from the specification. But Taylor notices something. Between cuts — in the moment when Johannsen repositions the work piece, selects the next tool, sets up the next operation — there is a quality to his movement that the other operators don't have. He isn't faster. He's *more fluid*. The transitions between specified operations have a coherence that the specification doesn't address because the specification covers the operations, not the spaces between them.

Taylor starts timing the transitions. The other operators take, on average, 45 seconds between cuts. Johannsen takes 44. The difference is negligible.

But the *quality* of Johannsen's transitions is different. He positions the next piece while removing the current one. His tool selection anticipates the next three operations, not just the next one. His setup for cut number five begins during the execution of cut number three. The operations are specified. The *spaces between operations* are where Johannsen's expertise lives. And those spaces produce a compound effect — by the end of a shift, Johannsen has made no individual operation faster, but he's completed twelve more pieces than the next best operator.

Taylor stares at his notebook. He has measured every operation on the lathe to the hundredth of a second. He has never measured the transitions.

He considers measuring them. He could time every tool change, every repositioning, every setup. He could specify the transitions the way he specified the cuts. He could create a table of optimal transitions. He could eliminate Johannsen's space the way he eliminated the shoveler's.

And he knows — the garden conversation won't leave him alone — that if he does, the space will move somewhere else. To the foreman who has to interpret the transition tables. To the superintendent who has to decide when conditions deviate from the table's assumptions. To Taylor himself. The space doesn't disappear. It migrates to the point of judgment.

He writes:

*The specification covers the operations. It cannot cover the connections between operations without becoming a specification of the entire shift — which would require a specification of the entire shop — which would require a specification of the entire business. The space between operations is irreducible at the level of the operator. The question is whether Johannsen's space is better than a specification's.*

He crosses this out. He writes instead:

*Johannsen operates at the level of the shift. The tables operate at the level of the cut. The tables are optimal for each cut. Johannsen is optimal for the shift. These are not the same optimization. The tables cannot see the shift because they address each cut independently. Johannsen sees the shift because the spaces between cuts are where he holds the whole.*

Taylor puts his notebook down. He does not, that afternoon, create a table for transitions between lathe operations. This is the first time in his career he has decided not to measure something. He isn't sure what he's decided instead. He suspects it is something about *trust* — about whether the space between specified operations should be governed by a table or by a machinist who can hear the metal sing.

He doesn't have words for it yet. He won't, in his lifetime, find them. He will continue to build tables and specify operations and measure to the hundredth of a second. But he will never quite shake the image of the finch on the garden wall — how it arrived, considered, and departed according to no specification he could write. And how the garden was better for the space it left behind.

---

The design principle:

> *The purpose of specification is to free the unspecifiable to do its work.*

Taylor's tables didn't exist to control Johannsen. They existed to free his attention from the cuts — which were optimizable, specifiable, reproducible — so that his expertise could live in the transitions, where it produced the most value. The tables were the constraint. The transitions were the space. And the space was where it could do the most good.

---

## Where the space is wrong

Two stories about what happens when the space is in the wrong place.

### The decision that can't be made

A woman is renovating her kitchen. She has a budget. She has a timeline. She has preferences. She also has constraints she can see — the budget ceiling, the contractor's availability, the building code. Constraints she can feel but can't name — family expectations, an aesthetic sense she can't articulate. And constraints she genuinely can't know in advance — how the materials will look in her specific light, how she'll feel about the result in six months.

She freezes. She can't decide. Her goal is to get it right on the first try, but she doesn't have enough information to know what "right" looks like. She cycles between two strategies: insist on complete information before acting (impossible — some constraints are unknowable), or take tiny exploratory steps in all directions until the full space is mapped (exhausting and endless).

In the framework's terms: her constraints are opaque. The specified ones (budget, timeline) are visible. The implicit ones (expectations, taste) are in her weights — her trained judgment, accumulated over a lifetime. The unknowable ones (future emotional response) are genuinely outside her information set. She can't model her own constraints because the full policy isn't projected into her scope.

The framework predicts exactly what happens: opaque constraints reduce the portion of the decision surface spent on proposals that could actually succeed. The actor churns against invisible boundaries. The grade stays high — she's thinking constantly, evaluating endlessly — but effective work output drops to zero.

What would help? Not removing the constraints (they're real). Not demanding she decide without information (that's the "just pick one" advice that never works). Making the *visible* constraints visible. The budget isn't just a number — it's a range with soft and hard limits. The timeline isn't just a date — it has flex in some areas and not others. The expectations aren't just pressure — some are firm ("the family needs to eat dinner somewhere during the renovation") and some are negotiable.

Project the constraints into her scope. Let her see the shape of the space she's working in. Then her judgment — her actual expertise, her taste, her sense of what works — has a bounded region to operate in. The space for her decision is no longer the entire universe of possible kitchens. It's the region defined by the visible constraints, and within that region, her *ma* can do what it's good at.

The small deliberate steps she resisted — pick one element, commit, observe, adjust — are the exploration strategy the framework calls System 4 behavior. Each step is a fold: assess the current state, produce one decision, observe the result. Each successful step crystallizes a piece of the space from "unknown" to "explored." The ratchet turns. The territory of unknowns shrinks. Eventually the right direction becomes visible — not because she figured it out in advance, but because she narrowed the space through exploration.

Her insistence on one big correct jump was the demand for *simulation* (the strongest level of knowledge in the framework's terminology) where only *characterization* (knowing the shape of the options) was available. The mismatch between the strength of knowledge she demanded and the strength the situation could provide is itself a trust gap. She didn't trust the process to converge. She wanted guarantees the space couldn't provide.

The space was in the wrong place. She had too much space where she needed constraints (the unknowable outcomes) and too little where she needed freedom (the actual decision, once bounds were visible).

### The standards that weren't written down

An engineer is designing a system in a corporate environment. He submits a proposal. It comes back rejected: "doesn't conform to our standard model." He revises. Rejected again, different reason. He asks for the standards document. There isn't one. The standards are the judgment of a long-tenured employee — formed over years, never specified, never written down.

The project cost triples. Every design decision becomes a round-trip through the same opaque evaluation. The engineer can't model his own constraints because the policy isn't in his scope. He can't enumerate the expected paths because the evaluation function is trained (the employee's judgment), not specified (a document he could read).

In the framework's terms: the engineer is operating against a computation channel. His proposal (the input) goes into an opaque evaluation process (the employee's judgment), and the output is allow or deny with no rationale. He can't predict the verdict any more than the Harness can predict what a Bash command will do — the evaluation function is Turing-complete human judgment applied to a complex domain.

The cost tripling is supermodularity in action. The interaction between opaque constraints (the engineer couldn't predict which proposals would pass — high effective decision surface from his perspective) and broad scope (a complex project with many interacting design decisions) produced characterization difficulty that far exceeded what specified, visible standards would have cost. The same standards, written down, would have been a data channel — read the document, check against it, iterate. Instead he had a computation channel — submit and wait for a verdict he couldn't anticipate.

And there's a ratchet failure here too. The long-tenured employee had done Stage 1: discovery. Over a career, they'd learned what worked, what failed, what caused problems downstream. They had genuinely valuable knowledge. But they never did Stage 2: crystallization. The knowledge stayed in their weights. It never became specified infrastructure. So every new project had to re-traverse the same trust gap, paying the same cost, because the organization's accumulated knowledge was high *ma* where it should have been specified.

The space was in the wrong place. The engineer had too much space where he needed specification (the standards) and was probably too constrained where he needed freedom (the actual creative design work, once the standards were visible).

---

## The design principle

Both stories illustrate the same thing, from opposite sides.

The kitchen renovation had invisible constraints that paralyzed the decision-maker. The corporate environment had invisible standards that taxed the designer. In both cases, the space for judgment existed — but it was in the wrong place. It was in navigating opaque constraints rather than in the actual work.

The fix in both cases is the same:

**Specify what can be specified. Make the specified visible. Put the space where judgment actually adds value.**

The budget and the standards are specifiable. They're not unknowable — someone knows them. Making them visible (projecting constraints into the actor's scope, in the framework's language) moves the space from "guessing what's allowed" to "choosing what's best within the allowed."

This is the post 8 transparency principle — minimize the gap between the full policy and its projection into the actor's scope — applied to human situations. And it's the ratchet's design principle — crystallize knowledge into specified infrastructure — applied to organizational knowledge.

But the deeper principle is Basho's: the purpose of specifying is not to eliminate the space. It's to put the space where it can do the most good. Taylor's tables existed so Johannsen's attention could live in the transitions. Budget documents exist so the renovator's taste can focus on the choices that matter. Standards documents exist so the engineer's creativity can focus on the design, not on guessing what's allowed.

Constraint and freedom aren't opposed. Constraint in the right places creates freedom in the right places.

---

## What this means for agent architecture

The field of agent architecture asks: *how much autonomy?* The autonomy-level frameworks give you a spectrum from fully human-controlled to fully autonomous. The SAE driving levels. The Parasuraman-Sheridan-Wickens 10-level model. The Knight Institute's five levels from operator to observer. One knob, turned from low to high.

The Ma framework adds: *where should the autonomy live?*

A coding agent with a planning phase and an execution phase. The planner gets broad tools — read the codebase, reason about the change, explore approaches. High *ma*. Room for divergence. System 4 behavior: environmental intelligence, strategic scanning. The executor gets narrow tools — edit this file, run this test, within this sandbox. Low *ma*. Tight constraints. System 1 behavior: do the specified work.

Same total autonomy budget. But the placement matters more than the total.^[This is a testable claim. An experiment is planned that holds total ma budget approximately constant across three conditions (uniform, front-loaded planning, back-loaded execution) and measures system quality. The framework predicts front-loaded placement produces the highest quality. If uniform placement performs equally well, the placement principle doesn't hold and magnitude is sufficient. Results will be reported when available.] The planner's broad freedom is where the quality of the approach is determined. The executor's tight constraints are where reliability and safety are ensured. Restrict the planner and you get safe but mediocre plans. Free the executor and you get creative but unreliable execution. The design question isn't "how much?" — it's "where?"

And the co-domain funnel — the pattern of deep reasoning compressed through a narrow interface — is exactly this principle applied to boundaries. The reviewer runs Opus internally (high *ma*, broad exploration of the code's quality) and outputs Approve / Reject / RequestChanges (low *ma*, fully enumerable). The space is inside the funnel. The interface is tight. The constraint at the interface frees the processing inside to focus on what it's good at: judgment, assessment, the kind of evaluation that benefits from divergence.

The specified band isn't about eliminating *ma*. It's about placing it. The coordination layer (the Harness, System 2) must be specified — transparent, readable, auditable. That's where zero space is correct. The intelligence function (the fold over the Inferencer, System 4) benefits from broad *ma* — exploration, connection-making, the kind of processing that produces insights the specification couldn't anticipate. The control function (System 3, currently underdeveloped) needs enough *ma* to assess whether the current approach is working, but not so much that it becomes an opaque oracle.

Each component of the system has a right amount of space. The architecture is a map of where the space should be generous and where it should be zero. The magnitude knob is a coarse tool. The placement map is the design.

---

## The jump

There's a haiku attributed to Basho — the most famous one — that the Ma framework has been circling without knowing it:

> *Old pond. / Frog jumps in. / The sound of water.*

The frog is the input. The water is the output. The poem is about neither. It's about the moment between jump and sound — the space where the pond hasn't yet decided what kind of sound to make.

That space is *ma*. The framework measures it. Basho lived in it.

The framework's tools — the grade lattice, the trust gap, the specified band, the ratchet — are tools for shaping the pond. Making it the right depth. Clearing the water. Ensuring the frog has a surface to land on. All of that work is necessary. None of it determines whether the jump is good.

What determines whether the jump is good is something the framework deliberately sets aside: the quality of the traversal through the space. The thing Johannsen had in the transitions between cuts. The thing a renovator has when she finally sees the shape of her constraints and her taste clicks into focus. The thing an engineer has when the standards are visible and the creative work can begin.

The framework can't formalize this. That's not a limitation to fix. It's a boundary to respect. The framework is soil science — it measures pH, nitrogen, drainage, light. It creates optimal conditions. But the thing that makes one tomato extraordinary and the next one merely adequate — that's in the seed and the season and something that resists the instruments.

The framework gives us the soil science. The jump is the frog's business.

And the design principle that falls out — the one that nine posts of lattice theory and one 17th-century poet converge on — is this:

**The purpose of constraint is to create the conditions where the right thing can emerge from the space between actors.**

Not safety. Not predictability. Not auditability. Those are the mechanism. The purpose is the jump.

Put the space where it can do the most good.

---

## Suggested updates to existing posts

This essay surfaces a framing that was latent in the series but never stated. Several posts would benefit from brief additions that connect their specific arguments to the placement principle:

**Post 2 (The Space Between):** The section on interface *ma* vs internal *ma* already describes the co-domain funnel pattern — high internal *ma* compressed through low interface *ma*. Add a sentence connecting this to placement: "The funnel is a placement decision: broad space inside, narrow space at the boundary. The constraint at the interface exists to free the processing within."

**Post 7 (Computation Channels):** The sandbox section describes the sandbox as a "dynamics controller." Add the placement frame: "The sandbox doesn't eliminate computation. It places the boundary between what the agent *can* do (constrained by the sandbox) and what it *chooses* to do (its judgment within those constraints). The sandbox defines the pond. The agent's jump is inside it."

**Post 8 (The Specified Band):** The SELinux coda describes the cost of opaque constraints. Strengthen by connecting to the placement principle: "Opaque constraints don't reduce the space — they misplace it. The agent's decision surface is consumed by navigating invisible boundaries rather than doing useful work. Transparent constraints move the space from 'guessing what's allowed' to 'choosing what's best.'"

**Post 9 (Building With Ma):** The design rules are currently framed defensively — restrict, constrain, minimize. Add a closing note: "Each restriction is a placement decision. Restricting tools frees the model's attention for reasoning. Restricting scope frees it for the relevant context. Restricting the interface frees the internal processing for depth. The rules minimize *ma* at boundaries so that *ma* inside can do its work."

**The Configuration Ratchet:** The two-stage framing (discovery to crystallization) already implies placement — exploration happens at high *ma*, crystallization moves the solved parts to low *ma*, freeing the frontier for the next exploration. Make this explicit: "Each turn of the ratchet is a placement operation. It moves a piece of the problem from 'requires judgment' to 'handled by specification,' which moves the remaining space to the frontier where judgment is most needed."

**Coordination Is Not Control (planned essay):** The Beer decomposition already identifies where different kinds of space belong — System 2 (coordination, specified, zero space), System 3 (control, enough space to assess), System 4 (intelligence, broad space for exploration). Frame the Beer mapping as a placement map: each system function has a right amount of space, and the architecture's job is to ensure the space is in the right system.

---

*This essay emerged from a review conversation between Teague Sterling and Claude in March 2026. The Basho framing, the Taylor narrative, and the anecdotes were developed collaboratively. The sentence "the question is not whether the space exists — it's whether you've put it where it can do the most good" was produced by Claude during a creative exercise and selected by Teague as the reframing the series needed. The selection — knowing which sentence carries the weight — was the Principal's contribution. The generation was the Inferencer's. The space between them is where this essay lives.*

---

*Companion to [The Ma of Multi-Agent Systems](00-intro.md)*
