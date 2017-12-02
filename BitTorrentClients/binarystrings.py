# Here are three ways of generating sequential binary strings of arbitrary length.
# Thanks to @leftparen and @leftparen's roommate for the ideas!
import math
# Creating a list of numbers and converting each one to binary.
# Ex: generate_binary(5)
def generate_binaryc(n):

  # 2^(n-1)  2^n - 1 inclusive
  bin_arr = range(0, int(math.pow(2,n)))
  bin_arr = [bin(i)[2:] for i in bin_arr]

  # Prepending 0's to binary strings
  max_len = len(max(bin_arr, key=len))
  bin_arr = [i.zfill(max_len) for i in bin_arr]

  return bin_arr


# Start from 0 and continually adding 1 to the binary string
# Ex: generate_binary(5)
def generate_binary(n):

  bin_arr = []
  bin_str = [0] * n

  for i in xrange(0, int(math.pow(2,n))):

    bin_arr.append("".join(map(str,bin_str))[::-1])
    bin_str[0] += 1

    # Iterate through entire array if there carrying
    for j in xrange(0, len(bin_str) - 1):

      if bin_str[j] == 2:
        bin_str[j] = 0
        bin_str[j+1] += 1
        continue

      else:
        break


  return bin_arr
print generate_binary(5)

# Recursive string generation
# Ex: generate_binary(5 , [])
def generate_binary_a(n, l):

  if n == 0:
    return l
  else:
    if len(l) == 0:
      return generate_binary(n-1, ["0", "1"])
    else:
      return generate_binary(n-1, [i + "0" for i in l] + [i + "1" for i in l])
