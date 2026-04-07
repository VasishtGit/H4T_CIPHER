from manim import *

class MeanSeedsExplanation(Scene):
    def construct(self):
        # Step 1: Display histogram data
        histogram_data = VGroup(
            Text("3 seeds: 2 apples"),
            Text("4 seeds: 1 apple"),
            Text("5 seeds: 4 apples"),
            Text("6 seeds: 1 apple"),
            Text("7 seeds: 2 apples"),
            Text("8 seeds: 0 apples"),
            Text("9 seeds: 3 apples")
        ).arrange(DOWN, buff=0.5)
        
        self.play(Write(histogram_data))
        self.wait(1)
        
        # Step 2: Calculate total seeds
        total_seeds_text = Text("Total Seeds = ").move_to(histogram_data.get_center())
        self.play(Transform(histogram_data, total_seeds_text))
        
        calculations = VGroup(
            Text("3 * 2 = 6"),
            Text("4 * 1 = 4"),
            Text("5 * 4 = 20"),
            Text("6 * 1 = 6"),
            Text("7 * 2 = 14"),
            Text("8 * 0 = 0"),
            Text("9 * 3 = 27")
        ).arrange(DOWN, buff=0.3).next_to(total_seeds_text, DOWN, buff=0.5)
        
        self.play(FadeIn(calculations[0]))
        for calc in calculations[1:]:
            self.play(Transform(calculations[calculations.index(calc)-1], calc))
            self.wait(0.5)
        
        total_sum = Text("6 + 4 + 20 + 6 + 14 + 0 + 27 = 77")
        self.play(Transform(calculations, total_sum))
        self.wait(1)
        
        # Step 3: Calculate total apples
        total_apples_text = Text("Total Apples = ").move_to(total_sum.get_center())
        self.play(Transform(total_sum, total_apples_text))
        
        apples_sum = Text("2 + 1 + 4 + 1 + 2 + 0 + 3 = 13")
        self.play(Transform(total_apples_text, apples_sum))
        self.wait(1)
        
        # Step 4: Compute mean
        mean_text = Text("Mean = ").move_to(apples_sum.get_center())
        self.play(Transform(apples_sum, mean_text))
        
        division = Text("77 ÷ 13 ≈ 5.923")
        self.play(Transform(mean_text, division))
        self.wait(1)
        
        # Step 5: Compare with options
        options = VGroup(
            Text("A) 4"),
            Text("B) 5"),
            Text("C) 6"),
            Text("D) 7")
        ).arrange(DOWN, buff=0.5).next_to(division, DOWN, buff=0.5)
        
        self.play(FadeIn(options))
        self.play(Indicate(options[2], color=YELLOW))
        self.wait(2)
        
        # Final answer
        final_answer = Text("Final Answer: C) 6").move_to(options.get_center())
        self.play(Transform(options, final_answer))
        self.wait(3)