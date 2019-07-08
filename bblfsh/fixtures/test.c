unsigned long long fib(int n);

int main() {
    fib(12);
    return 0;
}

unsigned long long fib(int n) {
    return (n <= 1) ? 1ULL : fib(n-2) + fib(n-1);
}