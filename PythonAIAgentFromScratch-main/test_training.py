#!/usr/bin/env python3
"""
Test script for AI Agent Training Improvements
Tests knowledge retrieval accuracy, reduced searching, and manual training features.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import retrieve_knowledge, store_knowledge, train_agent, review_knowledge, run_agent
import json

def test_retrieval_accuracy():
    """Test improved knowledge retrieval with scoring."""
    print("🧪 Testing Knowledge Retrieval Accuracy...")

    # Add some test knowledge
    store_knowledge("what is python", "Python is a high-level programming language known for its simplicity and readability.")
    store_knowledge("python programming", "Python is used for web development, data science, AI, and automation.")
    store_knowledge("machine learning basics", "Machine learning is a subset of AI that enables systems to learn from data.")

    # Test queries
    test_queries = [
        "what is python",
        "python programming language",
        "machine learning",
        "unrelated query about weather"
    ]

    for query in test_queries:
        knowledge, score = retrieve_knowledge(query)
        print(f"Query: '{query}' -> Score: {score:.2f}, Knowledge: {knowledge[:100]}...")

    print("✅ Retrieval accuracy test completed.\n")

def test_manual_training():
    """Test manual training and review features."""
    print("🧪 Testing Manual Training Features...")

    # Train new knowledge
    train_agent("test topic", "This is a test knowledge entry for training.")

    # Review knowledge
    print("Reviewing knowledge base:")
    review_knowledge()

    print("✅ Manual training test completed.\n")

def test_agent_behavior():
    """Test agent behavior with sample queries to check reduced searching."""
    print("🧪 Testing Agent Behavior (Reduced Searching)...")

    # Test queries that should use knowledge
    test_queries = [
        "what is python",  # Should use stored knowledge
        "tell me about machine learning",  # Should use stored knowledge
        "what is the capital of France"  # May need to search
    ]

    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        try:
            response, knowledge_used, model = run_agent(query, [])
            print(f"Response: {response[:100]}...")
            print(f"Knowledge used: {bool(knowledge_used)}")
            print(f"Model: {model}")
        except Exception as e:
            print(f"Error: {e}")

    print("✅ Agent behavior test completed.\n")

def benchmark_knowledge_usage():
    """Benchmark knowledge usage vs searching."""
    print("📊 Benchmarking Knowledge Usage vs Searching...")

    queries = [
        "what is python",
        "python programming",
        "machine learning basics",
        "quantum physics",
        "artificial intelligence"
    ]

    knowledge_hits = 0
    total_queries = len(queries)

    for query in queries:
        knowledge, score = retrieve_knowledge(query)
        if knowledge and score > 0.3:  # Threshold for "good" knowledge
            knowledge_hits += 1
            print(f"✅ '{query}' -> Knowledge hit (score: {score:.2f})")
        else:
            print(f"❌ '{query}' -> Would search (score: {score:.2f})")

    hit_rate = knowledge_hits / total_queries * 100
    print(f"\n📈 Knowledge Hit Rate: {hit_rate:.1f}% ({knowledge_hits}/{total_queries})")
    print("✅ Benchmarking completed.\n")

if __name__ == "__main__":
    print("🚀 Starting AI Agent Training Tests...\n")

    test_retrieval_accuracy()
    test_manual_training()
    test_agent_behavior()
    benchmark_knowledge_usage()

    print("🎉 All tests completed! Check the output above for results.")
