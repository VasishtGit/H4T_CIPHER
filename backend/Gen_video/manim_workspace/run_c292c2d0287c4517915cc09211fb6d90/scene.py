class AverageSeedsScene(Scene):
    def construct(self):
        # Step 1: Display histogram data
        data_title = Text("Histogram Data:")
        self.play(Write(data_title))
        self.wait()

        data_points = VGroup(
            Text("3 seeds: 2 apples"),
            Text("4 seeds: 4 apples"),
            Text("5 seeds: 5 apples"),
            Text("6 seeds: 1 apple"),
            Text("7 seeds: 2 apples"),
            Text("9 seeds: 3 apples")
        )
        data_points.arrange(DOWN, buff=0.5)
        self.play(FadeIn(data_points))
        self.wait()

        # Step 2: Calculate total apples
        total_apples_title = Text("Total Apples:")
        self.play(Write(total_apples_title))
        self.wait()

        total_apples = Text("2 + 4 + 5 + 1 + 2 + 3 = 17")
        self.play(FadeIn(total_apples))
        self.wait()

        # Step 3: Calculate total seeds
        total_seeds_title = Text("Total Seeds:")
        self.play(Write(total_seeds_title))
        self.wait()

        total_seeds = VGroup(
            Text("3 × 2 = 6"),
            Text("4 × 4 = 16"),
            Text("5 × 5 = 25"),
            Text("6 × 1 = 6"),
            Text("7 × 2 = 14"),
            Text("9 × 3 = 27")
        )
        total_seeds.arrange(DOWN, buff=0.5)
        self.play(FadeIn(total_seeds))
        self.wait()

        total_seeds_sum = Text("6 + 16 + 25 + 6 + 14 + 27 = 94")
        self.play(FadeIn(total_seeds_sum))
        self.wait()

        # Step 4: Compute mean
        mean_title = Text("Mean = Total Seeds / Total Apples")
        self.play(Write(mean_title))
        self.wait()

        mean_value = Text("94 / 17 ≈ 5.529")
        self.play(FadeIn(mean_value))
        self.wait()

        # Step 5: Compare to options
        options_title = Text("Options: A) 4, B) 5, C) 6, D) 7")
        self.play(Write(options_title))
        self.wait()

        comparison_text = Text("5.529 is closer to 6 than 5")
        self.play(FadeIn(comparison_text))
        self.wait()

        final_answer = Text("Final Answer: C) 6")
        self.play(Write(final_answer))
        self.wait()