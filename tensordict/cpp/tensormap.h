#ifndef TensorMap_h
#define TensorMap_h

#include <memory>
#include <torch/extension.h>
#include <unordered_map>
#include <set>
#include <variant>
#include <string>
#include <iostream>
#include <vector>

namespace py = pybind11;

class TensorMap {
    typedef std::variant<torch::Tensor, TensorMap> node;
    typedef std::unordered_map<std::string, node> map;
    private:
        std::shared_ptr<map> internalMap;
        map* unsafeGetInternalMap() const {
            return internalMap.get();
        }

        node GetRecursive(map* currentMap, const py::tuple indices, const int index);
        void SetRecursive(map* currentMap, const py::tuple  indices, const int index, node value);
        void GetKeysRecursive(std::set<std::vector<std::string> >& result, std::vector<std::string>& currentPath, const node& currentNode);
        // TODO something about batch size

    public:
        TensorMap();
        ~TensorMap() = default;

        TensorMap(const TensorMap&) = default;
        TensorMap(TensorMap&&) = default;

        TensorMap& operator=(const TensorMap& other) & {
           internalMap = other.internalMap;
           return *this;
        }
        TensorMap& operator=(TensorMap& other) & {
            internalMap = std::move(other.internalMap);
            return *this;
        }

        bool is_same(const TensorMap& other) const noexcept {
            return this->internalMap == other.internalMap;
        }

        bool operator==(const TensorMap& other) const {
            return this->internalMap == other.internalMap;
        }

        bool operator!=(const TensorMap& other) const {
            return this->internalMap != other.internalMap;
        }

        // Index Single Point
        node GetAt(const std::string key) const;
        void SetTensorAt(const std::string key, const torch::Tensor& value);
        void SetMapAt(const std::string key, const TensorMap& value);
        // Index Path
        node GetAtPath(const py::tuple key);
        void SetTensorAtPath(const py::tuple key, const torch::Tensor& value);
        void SetMapAtPath(const py::tuple key, const TensorMap& value);
        // TODO add keys - check iterator
        std::set<std::vector<std::string> > GetKeys();
};

#endif