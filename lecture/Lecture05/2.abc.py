from collections.abc import Collection, Mapping


def filter_even_numbers(numbers: Collection[int]) -> list[int]:
    return [num for num in numbers if num % 2 == 0]

filter_even_numbers({1, 2, 3, 4, 5})
filter_even_numbers([1, 2, 3, 4, 5])
filter_even_numbers((1, 2, 3, 4, 5))


def get_keys_with_high_values(mapping: Mapping[str, int], threshold: int) -> list[str]:
    return [key for key, value in mapping.items() if value > threshold]

d = {"apple": 5, "banana": 15, "cherry": 20}
get_keys_with_high_values(d, 10)

# Every class which has implemented __contains__, __iter__ and __len__ methods can be Collection
# When we declare that numbers can be any Collection it means we need to perform operations which use only that functions.

# Mapping must have __getitem__, __iter__ and __len__ implemented.