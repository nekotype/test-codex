"""
3問のPythonクイズ。問題はOpenAI APIで生成し、正解/不正解で別アクションを実行します。

実行方法:
  python quiz.py

環境変数:
  OPENAI_API_KEY を設定するとAI生成が有効になります。
"""

import json
import os
import sys
from typing import List, Dict, Callable

Question = Dict[str, object]


def correct_action(index: int, question: Question) -> None:
    """正解時のアクション: メッセージを出してスコア加算を知らせる。"""
    print(f"  -> 正解！ポイント +1")


def incorrect_action(index: int, question: Question) -> None:
    """不正解時のアクション: 正解を教える。"""
    answer_idx = question["answer"]
    correct_choice = question["choices"][answer_idx]  # type: ignore[index]
    print(f"  -> 不正解... 正解は「{correct_choice}」")


def ask_question(index: int, question: Question) -> bool:
    print(f"Q{index + 1}. {question['text']}")
    for i, choice in enumerate(question["choices"], start=1):  # type: ignore[index]
        print(f"   {i}: {choice}")

    while True:
        user_input = input("あなたの答え (1-4): ").strip()
        if user_input in {"1", "2", "3", "4"}:
            break
        print("1〜4の番号で入力してください。")

    user_choice = int(user_input) - 1
    is_correct = user_choice == question["answer"]
    if is_correct:
        correct_action(index, question)
    else:
        incorrect_action(index, question)
    print()
    return is_correct


def generate_questions_via_ai() -> List[Question]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY が設定されていません。")

    try:
        from openai import OpenAI  # type: ignore
    except Exception as exc:  # pragma: no cover - 実行環境依存
        raise RuntimeError("openai パッケージを import できませんでした。") from exc

    client = OpenAI(api_key=api_key)
    prompt = (
        "日本語でPythonに関する4択のクイズを3問だけ作成してください。"
        "出力は次のJSON形式のみ: "
        '[{"text": "...", "choices": ["...", "...", "...", "..."], "answer": 0}, ...]'
        "answerは0始まりの正解インデックス。説明文や余計なテキストは含めないこと。"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=700,
        )
        content = response.choices[0].message.content or ""
        questions = json.loads(content)
    except Exception as exc:  # pragma: no cover - ネットワーク/API依存
        raise RuntimeError(f"AIで問題生成に失敗しました: {exc}") from exc

    if not isinstance(questions, list) or len(questions) != 3:
        raise ValueError("AIの応答形式が不正です。")
    return questions


def fallback_questions() -> List[Question]:
    """AIが使えない場合の3問セット（最終手段）。"""
    return [
        {
            "text": "Pythonでラムダ式を定義するキーワードは？",
            "choices": ["lambda", "func", "arrow", "lambda()"],
            "answer": 0,
        },
        {
            "text": "__name__ が \"__main__\" のときに実行される場所は？",
            "choices": ["インポート時", "直接実行時", "関数定義時", "コンパイル時"],
            "answer": 1,
        },
        {
            "text": "整数同士の割り算で小数を得る演算子は？",
            "choices": ["//", "/", "%", "*/"],
            "answer": 1,
        },
    ]


def main() -> None:
    try:
        questions = generate_questions_via_ai()
    except Exception as exc:
        print(f"[警告] AIで問題生成ができませんでした: {exc}", file=sys.stderr)
        print("代わりに組み込みの3問を出題します。\n")
        questions = fallback_questions()

    print("Pythonクイズを始めます。全部で3問、各問題に対して1〜4で回答してください。\n")
    score = 0
    for idx, question in enumerate(questions):
        if ask_question(idx, question):
            score += 1

    print(f"結果: {score} / {len(questions)} 点")
    if score == len(questions):
        print("全問正解！お見事です。")
    elif score >= len(questions) * 0.7:
        print("いい調子！もう少しでパーフェクト。")
    else:
        print("復習して再チャレンジしてみてください。")


if __name__ == "__main__":
    main()
